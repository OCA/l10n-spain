# Copyright 2021 Tecnativa - João Marques
# Copyright 2022 ForgeFlow - Lois Rilo
# Copyright 2011-2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Aures Tic - Almudena de la Puente <almudena@aurestic.es>
# Copyright 2023 Aures Tic - Jose Zambudio <jose@aurestic.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
import logging

from odoo import _, api, exceptions, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.modules.registry import Registry
from odoo.tools.float_utils import float_compare

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

_logger = logging.getLogger(__name__)

SII_STATES = [
    ("sent_modified", "Registered in SII but last modifications not sent"),
    ("cancelled", "Cancelled"),
    ("cancelled_modified", "Cancelled in SII but last modifications not sent"),
]
SII_VERSION = "1.1"
SII_MACRODATA_LIMIT = 100000000.0
SII_DATE_FORMAT = "%d-%m-%Y"


class SiiMixin(models.AbstractModel):
    _name = "sii.mixin"
    _inherit = "aeat.mixin"
    _description = "SII Mixin"

    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
    )
    sii_description = fields.Text(
        string="SII computed description",
        compute="_compute_sii_description",
        default="/",
        store=True,
        readonly=False,
        copy=False,
    )
    aeat_state = fields.Selection(
        selection_add=SII_STATES,
    )
    sii_csv = fields.Char(string="SII CSV", copy=False, readonly=True)
    sii_return = fields.Text(string="SII Return", copy=False, readonly=True)
    sii_refund_type = fields.Selection(
        selection=[
            # ('S', 'By substitution'), - Removed as not fully supported
            ("I", "By differences"),
        ],
        string="SII Refund Type",
        compute="_compute_sii_refund_type",
        store=True,
        readonly=False,
    )
    sii_account_registration_date = fields.Date(
        string="SII account registration date",
        readonly=True,
        copy=False,
        help="Indicates the account registration date set at the SII, which "
        "must be the date when the document is recorded in the system and "
        "is independent of the date of the accounting entry of the "
        "document",
    )
    sii_registration_key_domain = fields.Char(
        compute="_compute_sii_registration_key_domain",
        string="SII registration key domain",
    )
    sii_registration_key = fields.Many2one(
        comodel_name="aeat.sii.mapping.registration.keys",
        string="SII registration key",
        compute="_compute_sii_registration_key",
        store=True,
        readonly=False,
        # required=True, This is not set as required here to avoid the
        # set not null constraint warning
    )
    sii_registration_key_code = fields.Char(
        compute="_compute_sii_registration_key_code",
        readonly=True,
        string="SII Code",
    )
    sii_enabled = fields.Boolean(
        string="Enable SII",
        compute="_compute_sii_enabled",
    )
    sii_macrodata = fields.Boolean(
        string="MacroData",
        help="Check to confirm that the document has an absolute amount "
        "greater o equal to 100 000 000,00 euros.",
        compute="_compute_macrodata",
    )

    def _compute_sii_refund_type(self):
        self.sii_refund_type = False

    def _compute_sii_description(self):
        self.sii_description = "/"

    def _compute_sii_registration_key_domain(self):
        for document in self:
            mapping_key = document._get_mapping_key()
            if mapping_key in {"out_invoice", "out_refund"}:
                document.sii_registration_key_domain = "sale"
            elif mapping_key in {"in_invoice", "in_refund"}:
                document.sii_registration_key_domain = "purchase"
            else:
                document.sii_registration_key_domain = False

    @api.depends("fiscal_position_id")
    def _compute_sii_registration_key(self):
        for document in self:
            mapping_key = document._get_mapping_key()
            if document.fiscal_position_id:
                if "out" in mapping_key:
                    key = document.fiscal_position_id.sii_registration_key_sale
                else:
                    key = document.fiscal_position_id.sii_registration_key_purchase
                # Only assign sii_registration_key if it's set in the fiscal position
                if key:
                    document.sii_registration_key = key
            else:
                domain = [
                    ("code", "=", "01"),
                    (
                        "type",
                        "=",
                        "sale" if mapping_key.startswith("out_") else "purchase",
                    ),
                ]
                sii_key_obj = self.env["aeat.sii.mapping.registration.keys"]
                document.sii_registration_key = sii_key_obj.search(domain, limit=1)

    @api.depends("sii_registration_key")
    def _compute_sii_registration_key_code(self):
        """
        Para evitar tiempos de instalación largos en BBDD grandes, es necesario que
        sólo dependa de sii_registration_key, ya que en caso de añadirlo odoo buscará
        todos los movimientos y cuando escribamos el key, aunque sea un campo no almacenado
        A partir de v16.0 este cambio ya no es necesario, ya que el sistema ya revisa que el
        campo sea almacenado o que este visualizandose (en caché)
        """
        for record in self:
            record.sii_registration_key_code = record.sii_registration_key.code

    def _compute_sii_enabled(self):
        raise NotImplementedError

    def _compute_macrodata(self):
        for document in self:
            document.sii_macrodata = (
                float_compare(
                    abs(document._get_document_amount_total()),
                    SII_MACRODATA_LIMIT,
                    precision_digits=2,
                )
                >= 0
            )

    def _filter_sii_unlink_not_possible(self):
        """Filter records that we do not allow to be deleted, all those
        that are not in not_sent sii status."""
        return self.filtered(lambda rec: rec.aeat_state != "not_sent")

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sii(self):
        """Do not allow the deletion of records already sent to the SII."""
        if self._filter_sii_unlink_not_possible():
            raise exceptions.UserError(
                _("You cannot delete an invoice already registered at the SII.")
            )

    @api.model
    def _get_aeat_taxes_map(self, codes, date):
        """Return the codes that correspond to that sii map line codes.

        :param codes: List of code strings to get the mapping.
        :param date: Date to map
        :return: Recordset with the corresponding codes
        """
        map_obj = self.env["aeat.sii.map"].sudo()
        sii_map = map_obj.search(
            [
                "|",
                ("date_from", "<=", date),
                ("date_from", "=", False),
                "|",
                ("date_to", ">=", date),
                ("date_to", "=", False),
            ],
            limit=1,
        )
        tax_templates = sii_map.map_lines.filtered(lambda x: x.code in codes).taxes
        return self.company_id.get_taxes_from_templates(tax_templates)

    def _get_aeat_header(self, tipo_comunicacion=False, cancellation=False):
        """Builds SII send header

        :param tipo_comunicacion String 'A0': new reg, 'A1': modification
        :param cancellation Bool True when the communitacion es for document
            cancellation
        :return Dict with header data depending on cancellation
        """
        self.ensure_one()
        if not self.company_id.vat:
            raise UserError(
                _("No VAT configured for the company '{}'").format(self.company_id.name)
            )
        header = {
            "IDVersionSii": SII_VERSION,
            "Titular": {
                "NombreRazon": self.company_id.name[0:120],
                "NIF": self.company_id.partner_id._parse_aeat_vat_info()[2],
            },
        }
        if not cancellation:
            header.update({"TipoComunicacion": tipo_comunicacion})
        return header

    def _get_sii_jobs_field_name(self):
        raise NotImplementedError()

    def _cancel_sii_jobs(self):
        for queue in self.sudo().mapped(self._get_sii_jobs_field_name()):
            if queue.state == "started":
                return False
            elif queue.state in ("pending", "enqueued", "failed"):
                queue.unlink()
        return True

    def send_sii(self):
        """General public method for filtering out of the starting recordset the records
        that shouldn't be sent to the SII:

        - Documents of companies with SII not enabled (through sii_enabled).
        - Documents not applicable to be sent to SII (through sii_enabled).
        - Documents in non applicable states (for example, cancelled invoices).
        - Documents already sent to the SII.
        - Documents with sending jobs pending to be executed.
        """
        valid_states = self._get_valid_document_states()
        jobs_field_name = self._get_sii_jobs_field_name()
        for document in self:
            if (
                not document.sii_enabled
                or document.state not in valid_states
                or document.aeat_state in ["sent", "cancelled"]
            ):
                continue
            job_states = document.sudo().mapped(jobs_field_name).mapped("state")
            if any([x in ("started", "pending", "enqueued") for x in job_states]):
                continue
            document._process_sii_send()

    def _process_sii_send(self):
        """Process document sending to the SII. Adds general checks from
        configuration parameters and document availability for SII. If the
        document is to be sent the decides the send method: direct send or
        via connector depending on 'Use connector' configuration"""
        queue_obj = self.env["queue.job"].sudo()
        for record in self:
            company = record.company_id
            if not company.use_connector:
                record.confirm_one_document()
            else:
                eta = company._get_sii_eta()
                new_delay = (
                    record.sudo()
                    .with_context(company_id=company.id)
                    .with_delay(eta=eta if not record.aeat_send_failed else False)
                    .confirm_one_document()
                )
                job = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                setattr(record.sudo(), self._get_sii_jobs_field_name(), [(4, job.id)])

    def _bind_service(self, client, port_name, address=None):
        self.ensure_one()
        service = client._get_service("siiService")
        port = client._get_port(service, port_name)
        address = address or port.binding_options["address"]
        return client.create_service(port.binding.name, address)

    def _connect_params_aeat(self, mapping_key):
        self.ensure_one()
        agency = self.company_id.tax_agency_id
        if not agency:
            # We use spanish agency by default to keep old behavior with
            # ir.config parameters. In the future it might be good to reinforce
            # to explicitly set a tax agency in the company by raising an error
            # here.
            agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        return agency._connect_params_sii(mapping_key, self.company_id)

    def _get_sii_gen_type(self):
        """Make a choice for general invoice type

        Returns:
            int: 1 (National), 2 (Intracom), 3 (Export)
        """
        self.ensure_one()
        partner_ident = self.fiscal_position_id.sii_partner_identification_type
        if partner_ident:
            res = int(partner_ident)
        elif self.fiscal_position_id.name == "Régimen Intracomunitario":
            res = 2
        elif self.fiscal_position_id.name == "Régimen Extracomunitario":
            res = 3
        else:
            res = 1
        return res

    def _is_aeat_simplified_invoice(self):
        """Inheritable method to allow control when an
        invoice are simplified or normal"""
        partner = self._aeat_get_partner()
        return partner.aeat_simplified_invoice

    def _aeat_check_exceptions(self):
        """Inheritable method for exceptions control when sending SII invoices."""
        res = super()._aeat_check_exceptions()
        if self.company_id.sii_enabled:
            gen_type = self._get_sii_gen_type()
            partner = self._aeat_get_partner()
            country_code = self._get_aeat_country_code()
            is_simplified_invoice = self._is_aeat_simplified_invoice()
            if (
                (gen_type != 3 or country_code == "ES")
                and not partner.vat
                and not is_simplified_invoice
            ):
                raise UserError(_("The partner has not a VAT configured."))
            if not self.sii_enabled:
                raise UserError(_("This invoice is not SII enabled."))
        return res

    def _get_document_fiscal_date(self):
        raise NotImplementedError()

    def _get_document_fiscal_year(self):
        return fields.Date.to_date(self._get_document_fiscal_date()).year

    def _get_document_period(self):
        return "%02d" % fields.Date.to_date(self._get_document_fiscal_date()).month

    def _get_document_product_exempt(self, applied_taxes):
        raise NotImplementedError()

    def _get_sii_exempt_cause(self, applied_taxes):
        """Código de la causa de exención según 3.6 y 3.7 de la FAQ del SII.

        :param applied_taxes: Taxes that are exempt for filtering the lines.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        if gen_type == 2:
            return "E5"
        else:
            exempt_cause = False
            product_exempt_causes = self._get_document_product_exempt(applied_taxes)
            if len(product_exempt_causes) > 1:
                raise UserError(
                    _("Currently there's no support for multiple exempt causes.")
                )
            if product_exempt_causes:
                exempt_cause = product_exempt_causes.pop()
            elif (
                self.fiscal_position_id.sii_exempt_cause
                and self.fiscal_position_id.sii_exempt_cause != "none"
            ):
                exempt_cause = self.fiscal_position_id.sii_exempt_cause
            if gen_type == 3 and exempt_cause not in ["E2", "E3"]:
                exempt_cause = "E2"
            return exempt_cause

    def _get_tax_info(self):
        raise NotImplementedError()

    def _get_sii_tax_req(self, tax):
        """Get the associated req tax for the specified tax.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE linked tax.
        :return: REQ tax (or empty recordset) linked to the provided tax.
        """
        raise NotImplementedError()

    @api.model
    def _get_sii_tax_dict(self, tax_line, tax_lines):
        """Get the SII tax dictionary for the passed tax line.

        :param self: Single invoice record.
        :param tax_line: Tax line that is being analyzed.
        :param tax_lines: Dictionary of processed invoice taxes for further operations
            (like REQ).
        :return: A dictionary with the corresponding SII tax values.
        """
        tax = tax_line["tax"]
        tax_base_amount = tax_line["base"]
        if tax.amount_type == "group":
            tax_type = abs(tax.children_tax_ids.filtered("amount")[:1].amount)
        else:
            tax_type = abs(tax.amount)
        tax_dict = {"TipoImpositivo": str(tax_type), "BaseImponible": tax_base_amount}
        if self._get_mapping_key() in ["out_invoice", "out_refund"]:
            key = "CuotaRepercutida"
        else:
            key = "CuotaSoportada"
        tax_dict[key] = tax_line["amount"]
        # Recargo de equivalencia
        req_tax = self._get_sii_tax_req(tax)
        if req_tax:
            tax_dict["TipoRecargoEquivalencia"] = req_tax.amount
            tax_dict["CuotaRecargoEquivalencia"] = tax_lines[req_tax]["amount"]
        return tax_dict

    def _get_no_taxable_cause(self):
        self.ensure_one()
        return (
            self.fiscal_position_id.sii_no_taxable_cause
            or "ImporteTAIReglasLocalizacion"
        )

    def _is_sii_type_breakdown_required(self, taxes_dict):
        """Calculates if the block 'DesgloseTipoOperacion' is required for
        the invoice communication."""
        self.ensure_one()
        if "DesgloseFactura" not in taxes_dict:
            return False
        country_code = self._get_aeat_country_code()
        sii_gen_type = self._get_sii_gen_type()
        if "DesgloseTipoOperacion" in taxes_dict:
            # DesgloseTipoOperacion and DesgloseFactura are Exclusive
            return True
        elif sii_gen_type in (2, 3):
            # DesgloseTipoOperacion required for Intracommunity and
            # Export operations
            return True
        elif sii_gen_type == 1 and country_code != "ES":
            # DesgloseTipoOperacion required for national operations
            # with 'IDOtro' in the SII identifier block
            return True
        elif sii_gen_type == 1 and (self._aeat_get_partner().vat or "").startswith(
            "ESN"
        ):
            # DesgloseTipoOperacion required if customer's country is Spain and
            # has a NIF which starts with 'N'
            return True
        return False

    def _get_sii_out_taxes(self):  # noqa: C901
        """Get the taxes for sales documents.

        :param self: Single document record.
        """
        self.ensure_one()
        taxes_dict = {}
        date = self._get_document_fiscal_date()
        taxes_sfesb = self._get_aeat_taxes_map(["SFESB"], date)
        taxes_sfesbe = self._get_aeat_taxes_map(["SFESBE"], date)
        taxes_sfesisp = self._get_aeat_taxes_map(["SFESISP"], date)
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'])
        taxes_sfens = self._get_aeat_taxes_map(["SFENS"], date)
        taxes_sfess = self._get_aeat_taxes_map(["SFESS"], date)
        taxes_sfesse = self._get_aeat_taxes_map(["SFESSE"], date)
        taxes_sfesns = self._get_aeat_taxes_map(["SFESNS"], date)
        taxes_not_in_total = self._get_aeat_taxes_map(["NotIncludedInTotal"], date)
        taxes_not_in_total_neg = self._get_aeat_taxes_map(
            ["NotIncludedInTotalNegative"], date
        )
        base_not_in_total = self._get_aeat_taxes_map(["BaseNotIncludedInTotal"], date)
        not_in_amount_total = 0
        exempt_cause = self._get_sii_exempt_cause(taxes_sfesbe + taxes_sfesse)
        tax_lines = self._get_tax_info()
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            breakdown_taxes = taxes_sfesb + taxes_sfesisp + taxes_sfens + taxes_sfesbe
            if tax in taxes_not_in_total:
                not_in_amount_total += tax_line["amount"]
            elif tax in taxes_not_in_total_neg:
                not_in_amount_total -= tax_line["amount"]
            elif tax in base_not_in_total:
                not_in_amount_total += tax_line["base"]
            if tax in breakdown_taxes:
                tax_breakdown = taxes_dict.setdefault("DesgloseFactura", {})
            if tax in (taxes_sfesb + taxes_sfesbe + taxes_sfesisp):
                sub_dict = tax_breakdown.setdefault("Sujeta", {})
                # TODO l10n_es no tiene impuesto exento de bienes
                # corrientes nacionales
                if tax in taxes_sfesbe:
                    exempt_dict = sub_dict.setdefault(
                        "Exenta",
                        {"DetalleExenta": [{"BaseImponible": 0}]},
                    )
                    det_dict = exempt_dict["DetalleExenta"][0]
                    if exempt_cause:
                        det_dict["CausaExencion"] = exempt_cause
                    det_dict["BaseImponible"] += tax_line["base"]
                else:
                    sub_dict.setdefault(
                        "NoExenta",
                        {
                            "TipoNoExenta": ("S2" if tax in taxes_sfesisp else "S1"),
                            "DesgloseIVA": {"DetalleIVA": []},
                        },
                    )
                    not_ex_type = sub_dict["NoExenta"]["TipoNoExenta"]
                    if tax in taxes_sfesisp:
                        is_s3 = not_ex_type == "S1"
                    else:
                        is_s3 = not_ex_type == "S2"
                    if is_s3:
                        sub_dict["NoExenta"]["TipoNoExenta"] = "S3"
                    sub_dict["NoExenta"]["DesgloseIVA"]["DetalleIVA"].append(
                        self._get_sii_tax_dict(tax_line, tax_lines),
                    )
            # No sujetas
            if tax in taxes_sfens:
                # ImporteTAIReglasLocalizacion or ImportePorArticulos7_14_Otros
                default_no_taxable_cause = self._get_no_taxable_cause()
                nsub_dict = tax_breakdown.setdefault(
                    "NoSujeta",
                    {default_no_taxable_cause: 0},
                )
                nsub_dict[default_no_taxable_cause] += tax_line["base"]
            if tax in (taxes_sfess + taxes_sfesse + taxes_sfesns):
                type_breakdown = taxes_dict.setdefault(
                    "DesgloseTipoOperacion",
                    {"PrestacionServicios": {}},
                )
                if tax in (taxes_sfesse + taxes_sfess):
                    type_breakdown["PrestacionServicios"].setdefault("Sujeta", {})
                service_dict = type_breakdown["PrestacionServicios"]
                if tax in taxes_sfesse:
                    exempt_dict = service_dict["Sujeta"].setdefault(
                        "Exenta",
                        {"DetalleExenta": [{"BaseImponible": 0}]},
                    )
                    det_dict = exempt_dict["DetalleExenta"][0]
                    if exempt_cause:
                        det_dict["CausaExencion"] = exempt_cause
                    det_dict["BaseImponible"] += tax_line["base"]
                if tax in taxes_sfess:
                    # TODO l10n_es_ no tiene impuesto ISP de servicios
                    # if tax in taxes_sfesisps:
                    #     TipoNoExenta = 'S2'
                    # else:
                    service_dict["Sujeta"].setdefault(
                        "NoExenta",
                        {"TipoNoExenta": "S1", "DesgloseIVA": {"DetalleIVA": []}},
                    )
                    sub = type_breakdown["PrestacionServicios"]["Sujeta"]["NoExenta"][
                        "DesgloseIVA"
                    ]["DetalleIVA"]
                    sub.append(self._get_sii_tax_dict(tax_line, tax_lines))
                if tax in taxes_sfesns:
                    nsub_dict = service_dict.setdefault(
                        "NoSujeta",
                        {"ImporteTAIReglasLocalizacion": 0},
                    )
                    nsub_dict["ImporteTAIReglasLocalizacion"] += tax_line["base"]
        # Ajustes finales breakdown
        # - DesgloseFactura y DesgloseTipoOperacion son excluyentes
        # - Ciertos condicionantes obligan DesgloseTipoOperacion
        if self._is_sii_type_breakdown_required(taxes_dict):
            taxes_dict.setdefault("DesgloseTipoOperacion", {})
            taxes_dict["DesgloseTipoOperacion"]["Entrega"] = taxes_dict[
                "DesgloseFactura"
            ]
            del taxes_dict["DesgloseFactura"]
        return taxes_dict, not_in_amount_total

    def _get_sii_invoice_type(self):
        raise NotImplementedError()

    def _get_sii_identifier(self):
        """Get the SII structure for a partner identifier depending on the
        conditions of the invoice.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        (
            country_code,
            identifier_type,
            identifier,
        ) = self._aeat_get_partner()._parse_aeat_vat_info()
        # Limpiar alfanum
        if identifier:
            identifier = "".join(e for e in identifier if e.isalnum()).upper()
        else:
            identifier = "NO_DISPONIBLE"
            identifier_type = "06"
        if gen_type == 1:
            if "1117" in (self.aeat_send_error or ""):
                return {
                    "IDOtro": {
                        "CodigoPais": country_code,
                        "IDType": "07",
                        "ID": identifier,
                    }
                }
            else:
                if identifier_type == "":
                    return {"NIF": identifier}
                return {
                    "IDOtro": {
                        "CodigoPais": country_code,
                        "IDType": identifier_type,
                        "ID": country_code + identifier
                        if self._aeat_get_partner()._map_aeat_country_code(country_code)
                        in self._aeat_get_partner()._get_aeat_europe_codes()
                        else identifier,
                    },
                }
        elif gen_type == 2:
            return {"IDOtro": {"IDType": "02", "ID": country_code + identifier}}
        elif gen_type == 3 and identifier_type:
            # Si usamos identificador tipo 02 en exportaciones, el envío falla con:
            #   {'CodigoErrorRegistro': 1104,
            #    'DescripcionErrorRegistro': 'Valor del campo ID incorrecto'}
            if identifier_type == "02":
                identifier_type = "06"
            return {
                "IDOtro": {
                    "CodigoPais": country_code,
                    "IDType": identifier_type,
                    "ID": identifier,
                },
            }
        elif gen_type == 3:
            return {"NIF": identifier}

    def _get_aeat_invoice_dict_out(self, cancel=False):
        """Build dict with data to send to AEAT WS for document types:
        out_invoice and out_refund.

        :param cancel: It indicates if the dictionary is for sending a
          cancellation of the document.
        :return: documents (dict) : Dict XML with data for this document.
        """
        self.ensure_one()
        document_date = self._change_date_format(self._get_document_date())
        partner = self._aeat_get_partner()
        company = self.company_id
        fiscal_year = self._get_document_fiscal_year()
        period = self._get_document_period()
        is_simplified_invoice = self._is_aeat_simplified_invoice()
        serial_number = self._get_document_serial_number()
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {
                    "NIF": company.partner_id._parse_aeat_vat_info()[2]
                },
                # On cancelled invoices, number is not filled
                "NumSerieFacturaEmisor": serial_number,
                "FechaExpedicionFacturaEmisor": document_date,
            },
            "PeriodoLiquidacion": {
                "Ejercicio": fiscal_year,
                "Periodo": period,
            },
        }
        if not cancel:
            tipo_desglose, not_in_amount_total = self._get_sii_out_taxes()
            amount_total = self._get_document_amount_total() - not_in_amount_total
            inv_dict["FacturaExpedida"] = {
                "TipoFactura": self._get_sii_invoice_type(),
                "ClaveRegimenEspecialOTrascendencia": (self.sii_registration_key.code),
                "DescripcionOperacion": self.sii_description,
                "TipoDesglose": tipo_desglose,
                "ImporteTotal": amount_total,
            }
            if self.sii_macrodata:
                inv_dict["FacturaExpedida"].update(Macrodato="S")
            exp_dict = inv_dict["FacturaExpedida"]
            if not is_simplified_invoice:
                # Simplified invoices don't have counterpart
                exp_dict["Contraparte"] = {
                    "NombreRazon": partner.name[0:120],
                }
                # Uso condicional de IDOtro/NIF
                exp_dict["Contraparte"].update(self._get_sii_identifier())
        return inv_dict

    def _get_aeat_invoice_dict_in(self, cancel=False):
        """Build dict with data to send to AEAT WS for invoice types:
        in_invoice and in_refund.

        :param cancel: It indicates if the dictionary if for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        raise NotImplementedError()

    def _get_aeat_invoice_dict(self):
        self.ensure_one()
        self._aeat_check_exceptions()
        inv_dict = {}
        mapping_key = self._get_mapping_key()
        if mapping_key in ["out_invoice", "out_refund"]:
            inv_dict = self._get_aeat_invoice_dict_out()
        elif mapping_key in ["in_invoice", "in_refund"]:
            inv_dict = self._get_aeat_invoice_dict_in()
        round_by_keys(
            inv_dict,
            [
                "BaseImponible",
                "CuotaRepercutida",
                "CuotaSoportada",
                "TipoRecargoEquivalencia",
                "CuotaRecargoEquivalencia",
                "ImportePorArticulos7_14_Otros",
                "ImporteTAIReglasLocalizacion",
                "ImporteTotal",
                "BaseRectificada",
                "CuotaRectificada",
                "CuotaDeducible",
                "ImporteCompensacionREAGYP",
            ],
        )
        return inv_dict

    def _get_account_registration_date(self):
        """Hook method to allow the setting of the account registration date
        of each supplier invoice. The SII recommends to set the send date as
        the default value (point 9.3 of the document
        SII_Descripcion_ServicioWeb_v0.7.pdf), so by default we return
        the current date or, if exists, the stored
        sii_account_registration_date
        :return String date in the format %Y-%m-%d"""
        self.ensure_one()
        return self.sii_account_registration_date or fields.Date.today()

    def _send_document_to_sii(self):
        for document in self.filtered(
            lambda i: i.state in self._get_valid_document_states()
        ):
            if document.aeat_state == "not_sent":
                tipo_comunicacion = "A0"
            else:
                tipo_comunicacion = "A1"
            header = document._get_aeat_header(tipo_comunicacion)
            doc_vals = {
                "aeat_header_sent": json.dumps(header, indent=4),
            }
            # add this extra try except in case _get_aeat_invoice_dict fails
            # if not, get the value doc_dict for the next try and except below
            try:
                inv_dict = document._get_aeat_invoice_dict()
            except Exception as fault:
                raise ValidationError(fault) from fault
            try:
                mapping_key = document._get_mapping_key()
                serv = document._connect_aeat(mapping_key)
                doc_vals["aeat_content_sent"] = json.dumps(inv_dict, indent=4)
                if mapping_key in ["out_invoice", "out_refund"]:
                    res = serv.SuministroLRFacturasEmitidas(header, inv_dict)
                elif mapping_key in ["in_invoice", "in_refund"]:
                    res = serv.SuministroLRFacturasRecibidas(header, inv_dict)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position_id.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.SuministroLRDetOperacionIntracomunitaria(
                #         header, invoices)
                res_line = res["RespuestaLinea"][0]
                if res["EstadoEnvio"] == "Correcto":
                    doc_vals.update(
                        {
                            "aeat_state": "sent",
                            "sii_csv": res["CSV"],
                            "aeat_send_failed": False,
                        }
                    )
                elif (
                    res["EstadoEnvio"] == "ParcialmenteCorrecto"
                    and res_line["EstadoRegistro"] == "AceptadoConErrores"
                ):
                    doc_vals.update(
                        {
                            "aeat_state": "sent_w_errors",
                            "sii_csv": res["CSV"],
                            "aeat_send_failed": True,
                        }
                    )
                else:
                    doc_vals["aeat_send_failed"] = True
                if (
                    "aeat_state" in doc_vals
                    and not document.sii_account_registration_date
                    and mapping_key[:2] == "in"
                ):
                    doc_vals[
                        "sii_account_registration_date"
                    ] = self._get_account_registration_date()
                doc_vals["sii_return"] = res
                send_error = False
                if res_line["CodigoErrorRegistro"]:
                    send_error = "{} | {}".format(
                        str(res_line["CodigoErrorRegistro"]),
                        str(res_line["DescripcionErrorRegistro"])[:60],
                    )
                doc_vals["aeat_send_error"] = send_error
                document.write(doc_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                document = env[document._name].browse(document.id)
                doc_vals.update(
                    {
                        "aeat_send_failed": True,
                        "aeat_send_error": repr(fault)[:60],
                        "sii_return": repr(fault),
                        "aeat_content_sent": json.dumps(inv_dict, indent=4),
                    }
                )
                document.write(doc_vals)
                new_cr.commit()
                new_cr.close()
                raise ValidationError(fault) from fault

    def confirm_one_document(self):
        self.sudo()._send_document_to_sii()
