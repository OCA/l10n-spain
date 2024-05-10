# Copyright 2017 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2017 Studio73 - Pablo Fuentes <pablo@studio73>
# Copyright 2017 Studio73 - Jordi Tolsà <jordi@studio73.es>
# Copyright 2018 Javi Melendez <javimelex@gmail.com>
# Copyright 2018 PESOL - Angel Moya <angel.moya@pesol.es>
# Copyright 2020 Valentin Vinagre <valent.vinagre@sygel.es>
# Copyright 2021 Tecnativa - João Marques
# Copyright 2022 ForgeFlow - Lois Rilo
# Copyright 2011-2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Aures Tic - Almudena de la Puente <almudena@aurestic.es>
# Copyright 2023 Aures Tic - Jose Zambudio <jose@aurestic.es>
# Copyright 2023 Moduon Team - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json
import logging

from odoo import _, api, exceptions, fields, models
from odoo.modules.registry import Registry

SII_VALID_INVOICE_STATES = ["posted"]
_logger = logging.getLogger(__name__)


try:
    from odoo.addons.queue_job.job import job
except ImportError:
    _logger.debug("Can not `import queue_job`.")
    import functools

    def empty_decorator_factory(*argv, **kwargs):
        return functools.partial

    job = empty_decorator_factory


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "sii.mixin"]

    def _get_default_type(self):
        context = self.env.context
        return context.get("move_type", context.get("default_move_type"))

    def _default_sii_refund_type(self):
        inv_type = self._get_default_type()
        return "I" if inv_type in ["out_refund", "in_refund"] else False

    sii_refund_specific_invoice_type = fields.Selection(
        selection=[
            ("R1", "Error based on law and Art. 80 One and Two LIVA (R1)"),
            ("R2", "Art. 80 Three LIVA - Bankruptcy (R2)"),
            ("R3", "Art. 80 Four LIVA - Bad debt (R3)"),
            ("R4", "Rest of causes (R4)"),
        ],
        help="Fill this field when the refund are one of the specific cases"
        " of article 80 of LIVA for notifying to SII with the proper"
        " invoice type.",
    )
    sii_registration_key_additional1 = fields.Many2one(
        comodel_name="aeat.sii.mapping.registration.keys",
        string="Additional SII registration key",
    )
    sii_registration_key_additional2 = fields.Many2one(
        comodel_name="aeat.sii.mapping.registration.keys",
        string="Additional 2 SII registration key",
    )
    sii_property_location = fields.Selection(
        string="Real property location",
        copy=False,
        selection=[
            (
                "1",
                "[1]-Real property with cadastral code located within "
                "the Spanish territory except Basque Country or Navarra",
            ),
            ("2", "[2]-Real property located in the " "Basque Country or Navarra"),
            (
                "3",
                "[3]-Real property in any of the above situations "
                "but without cadastral code",
            ),
            ("4", "[4]-Real property located in a foreign country"),
        ],
    )
    sii_property_cadastrial_code = fields.Char(
        string="Real property cadastrial code",
        copy=False,
    )
    sii_lc_operation = fields.Boolean(
        string="Customs - Complementary settlement",
        help="Check this mark if this invoice represents a complementary "
        "settlement for customs.\n"
        "The invoice number should start with LC, QZC, QRC, A01 or A02.",
        copy=False,
    )
    invoice_jobs_ids = fields.Many2many(
        comodel_name="queue.job",
        column1="invoice_id",
        column2="job_id",
        relation="account_move_queue_job_rel",
        string="Connector Jobs",
        copy=False,
    )

    @api.depends("move_type")
    def _compute_sii_refund_type(self):
        for record in self:
            if "refund" in (record.move_type or ""):
                record.sii_refund_type = "I"
            else:
                record.sii_refund_type = False

    @api.depends("move_type")
    def _compute_sii_registration_key_domain(self):
        return super()._compute_sii_registration_key_domain()

    @api.depends("move_type")
    def _compute_sii_registration_key(self):
        return super()._compute_sii_registration_key()

    @api.depends("amount_total")
    def _compute_macrodata(self):
        return super()._compute_macrodata()

    def _aeat_get_partner(self):
        return self.commercial_partner_id

    def _raise_exception_sii(self, field_name):
        raise exceptions.UserError(
            _(
                "You cannot change the %s of an invoice "
                "already registered at the SII. You must cancel the "
                "invoice and create a new one with the correct value"
            )
            % field_name
        )

    def write(self, vals):
        """For supplier invoices the SII primary key is the supplier
        VAT/ID Otro and the supplier invoice number. Cannot let change these
        values in a SII registered supplier invoice"""
        for invoice in self.filtered(
            lambda x: x.is_invoice() and x.aeat_state != "not_sent"
        ):
            if "invoice_date" in vals:
                self._raise_exception_sii(_("invoice date"))
            elif "thirdparty_number" in vals:
                self._raise_exception_sii(_("third-party number"))
            if invoice.move_type in ["in_invoice", "in_refund"]:
                if "partner_id" in vals:
                    correct_partners = invoice._aeat_get_partner()
                    correct_partners |= correct_partners.child_ids
                    if vals["partner_id"] not in correct_partners.ids:
                        self._raise_exception_sii(_("supplier"))
                elif "ref" in vals:
                    self._raise_exception_sii(_("supplier invoice number"))
            elif invoice.move_type in ["out_invoice", "out_refund"]:
                if "name" in vals:
                    self._raise_exception_sii(_("invoice number"))
        return super().write(vals)

    def _filter_sii_unlink_not_possible(self):
        """Filter records that we can delete to apply only to invoices."""
        res = super()._filter_sii_unlink_not_possible()
        return res.filtered(lambda x: x.is_invoice())

    def _get_sii_tax_req(self, tax):
        """Get the associated req tax for the specified tax.

        :param self: Single invoice record.
        :param tax: Initial tax for searching for the RE linked tax.
        :return: REQ tax (or empty recordset) linked to the provided tax.
        """
        self.ensure_one()
        taxes_req = self._get_aeat_taxes_map(["RE"], self._get_document_fiscal_date())
        re_lines = self.line_ids.filtered(
            lambda x: tax in x.tax_ids and x.tax_ids & taxes_req
        )
        req_tax = re_lines.mapped("tax_ids") & taxes_req
        if len(req_tax) > 1:
            raise exceptions.UserError(
                _("There's a mismatch in taxes for RE. Check them.")
            )
        return req_tax

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
        if self.move_type in ["out_invoice", "out_refund"]:
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

    def _get_document_amount_total(self):
        return self.amount_total_signed

    def _get_sii_out_taxes(self):  # noqa: C901
        """Get the taxes for sales invoices.

        :param self: Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_sfesb = self._get_aeat_taxes_map(["SFESB"], self.date)
        taxes_sfesbe = self._get_aeat_taxes_map(["SFESBE"], self.date)
        taxes_sfesisp = self._get_aeat_taxes_map(["SFESISP"], self.date)
        # taxes_sfesisps = self._get_taxes_map(['SFESISPS'])
        taxes_sfens = self._get_aeat_taxes_map(["SFENS"], self.date)
        taxes_sfess = self._get_aeat_taxes_map(["SFESS"], self.date)
        taxes_sfesse = self._get_aeat_taxes_map(["SFESSE"], self.date)
        taxes_sfesns = self._get_aeat_taxes_map(["SFESNS"], self.date)
        taxes_not_in_total = self._get_aeat_taxes_map(["NotIncludedInTotal"], self.date)
        taxes_not_in_total_neg = self._get_aeat_taxes_map(
            ["NotIncludedInTotalNegative"], self.date
        )
        base_not_in_total = self._get_aeat_taxes_map(
            ["BaseNotIncludedInTotal"], self.date
        )
        not_in_amount_total = 0
        exempt_cause = self._get_sii_exempt_cause(taxes_sfesbe + taxes_sfesse)
        tax_lines = self._get_aeat_tax_info()
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

    @api.model
    def _merge_tax_dict(self, vat_list, tax_dict, comp_key, merge_keys):
        """Helper method for merging values in an existing tax dictionary."""
        for existing_dict in vat_list:
            if existing_dict.get(comp_key, "-99") == tax_dict.get(comp_key, "-99"):
                for key in merge_keys:
                    existing_dict[key] += tax_dict[key]
                return True
        return False

    def _get_sii_in_taxes(self):
        """Get the taxes for purchase invoices.

        :param self:  Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        taxes_sfrs = self._get_aeat_taxes_map(["SFRS"], self.date)
        taxes_sfrsa = self._get_aeat_taxes_map(["SFRSA"], self.date)
        taxes_sfrisp = self._get_aeat_taxes_map(["SFRISP"], self.date)
        taxes_sfrns = self._get_aeat_taxes_map(["SFRNS"], self.date)
        taxes_sfrnd = self._get_aeat_taxes_map(["SFRND"], self.date)
        taxes_sfrbi = self._get_aeat_taxes_map(["SFRBI"], self.date)
        taxes_not_in_total = self._get_aeat_taxes_map(["NotIncludedInTotal"], self.date)
        taxes_not_in_total_neg = self._get_aeat_taxes_map(
            ["NotIncludedInTotalNegative"], self.date
        )
        base_not_in_total = self._get_aeat_taxes_map(
            ["BaseNotIncludedInTotal"], self.date
        )
        tax_amount = 0.0
        not_in_amount_total = 0.0
        tax_lines = self._get_aeat_tax_info()
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            if tax in taxes_not_in_total:
                not_in_amount_total += tax_line["amount"]
            elif tax in taxes_not_in_total_neg:
                not_in_amount_total -= tax_line["amount"]
            elif tax in base_not_in_total:
                not_in_amount_total += tax_line["base"]
            if tax in taxes_sfrisp:
                base_dict = taxes_dict.setdefault(
                    "InversionSujetoPasivo",
                    {"DetalleIVA": []},
                )
            elif tax in taxes_sfrs + taxes_sfrns + taxes_sfrsa + taxes_sfrnd:
                base_dict = taxes_dict.setdefault("DesgloseIVA", {"DetalleIVA": []})
            else:
                continue
            tax_dict = self._get_sii_tax_dict(tax_line, tax_lines)
            if tax in taxes_sfrisp + taxes_sfrs:
                tax_amount += tax_line["deductible_amount"]
            if tax in taxes_sfrbi:
                tax_dict["BienInversion"] = "S"
            if tax in taxes_sfrns:
                tax_dict.pop("TipoImpositivo")
                tax_dict.pop("CuotaSoportada")
                base_dict["DetalleIVA"].append(tax_dict)
            elif tax in taxes_sfrsa:
                tax_dict["PorcentCompensacionREAGYP"] = tax_dict.pop("TipoImpositivo")
                tax_dict["ImporteCompensacionREAGYP"] = tax_dict.pop("CuotaSoportada")
                base_dict["DetalleIVA"].append(tax_dict)
            else:
                if not self._merge_tax_dict(
                    base_dict["DetalleIVA"],
                    tax_dict,
                    "TipoImpositivo",
                    ["BaseImponible", "CuotaSoportada"],
                ):
                    base_dict["DetalleIVA"].append(tax_dict)
        return taxes_dict, tax_amount, not_in_amount_total

    def _get_mapping_key(self):
        return self.move_type

    def _aeat_check_exceptions(self):
        res = super()._aeat_check_exceptions()
        is_simplified_invoice = self._is_aeat_simplified_invoice()
        if is_simplified_invoice and self.move_type[:2] == "in":
            raise exceptions.UserError(
                _("You can't make a supplier simplified invoice.")
            )
        if not self.ref and self.move_type in ["in_invoice", "in_refund"]:
            raise exceptions.UserError(_("The supplier number invoice is required"))
        return res

    def _get_sii_invoice_type(self):
        invoice_type = ""
        if self.sii_lc_operation:
            return "LC"
        if self.move_type in ["in_invoice", "in_refund"]:
            invoice_type = "R4" if self.move_type == "in_refund" else "F1"
        elif self.move_type in ["out_invoice", "out_refund"]:
            is_simplified = self._is_aeat_simplified_invoice()
            invoice_type = "F2" if is_simplified else "F1"
            if self.move_type == "out_refund":
                if self.sii_refund_specific_invoice_type:
                    invoice_type = self.sii_refund_specific_invoice_type
                else:
                    invoice_type = "R5" if is_simplified else "R1"
        return invoice_type

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if cancel:
            return inv_dict
        if self.thirdparty_invoice:
            inv_dict["FacturaExpedida"]["EmitidaPorTercerosODestinatario"] = "S"
        if self.sii_registration_key_additional1:
            inv_dict["FacturaExpedida"].update(
                {
                    "ClaveRegimenEspecialOTrascendenciaAdicional1": (
                        self.sii_registration_key_additional1.code
                    )
                }
            )
        if self.sii_registration_key_additional2:
            inv_dict["FacturaExpedida"].update(
                {
                    "ClaveRegimenEspecialOTrascendenciaAdicional2": (
                        self.sii_registration_key_additional2.code
                    )
                }
            )
        if self.sii_registration_key.code in ["12", "13"]:
            inv_dict["FacturaExpedida"]["DatosInmueble"] = {
                "DetalleInmueble": {
                    "SituacionInmueble": self.sii_property_location,
                    "ReferenciaCatastral": (self.sii_property_cadastrial_code or ""),
                }
            }
        exp_dict = inv_dict["FacturaExpedida"]
        if self.move_type == "out_refund":
            exp_dict["TipoRectificativa"] = self.sii_refund_type
            if self.sii_refund_type == "S":
                origin = self.refund_invoice_id
                exp_dict["ImporteRectificacion"] = {
                    "BaseRectificada": abs(origin.amount_untaxed_signed),
                    "CuotaRectificada": abs(
                        origin.amount_total_signed - origin.amount_untaxed_signed
                    ),
                }
        return inv_dict

    def _get_document_date(self):
        return self.invoice_date

    def _get_document_fiscal_date(self):
        return self.date

    def _get_document_serial_number(self):
        serial_number = (self.name or "")[0:60]
        if self.thirdparty_invoice:
            serial_number = self.thirdparty_number[0:60]
        return serial_number

    def _get_aeat_invoice_dict_in(self, cancel=False):
        """Build dict with data to send to AEAT WS for invoice types:
        in_invoice and in_refund.

        :param cancel: It indicates if the dictionary if for sending a
          cancellation of the invoice.
        :return: invoices (dict) : Dict XML with data for this invoice.
        """
        self.ensure_one()
        invoice_date = self._change_date_format(self.invoice_date)
        reg_date = self._change_date_format(self._get_account_registration_date())
        ejercicio = fields.Date.to_date(self.date).year
        periodo = "%02d" % fields.Date.to_date(self.date).month
        partner = self._aeat_get_partner()
        desglose_factura, tax_amount, not_in_amount_total = self._get_sii_in_taxes()
        inv_dict = {
            "IDFactura": {
                "IDEmisorFactura": {},
                "NumSerieFacturaEmisor": ((self.ref or "")[:60]),
                "FechaExpedicionFacturaEmisor": invoice_date,
            },
            "PeriodoLiquidacion": {"Ejercicio": ejercicio, "Periodo": periodo},
        }
        # Uso condicional de IDOtro/NIF
        ident = self._get_sii_identifier()
        inv_dict["IDFactura"]["IDEmisorFactura"].update(ident)
        if cancel:
            inv_dict["IDFactura"]["IDEmisorFactura"].update(
                {"NombreRazon": partner.name[0:120]}
            )
        else:
            amount_total = -self.amount_total_signed - not_in_amount_total
            inv_dict["FacturaRecibida"] = {
                # TODO: Incluir los 5 tipos de facturas rectificativas
                "TipoFactura": self._get_sii_invoice_type(),
                "ClaveRegimenEspecialOTrascendencia": self.sii_registration_key.code,
                "DescripcionOperacion": self.sii_description,
                "DesgloseFactura": desglose_factura,
                "Contraparte": {"NombreRazon": partner.name[0:120]},
                "FechaRegContable": reg_date,
                "ImporteTotal": amount_total,
                "CuotaDeducible": tax_amount,
            }
            if self.sii_macrodata:
                inv_dict["FacturaRecibida"].update(Macrodato="S")
            if self.sii_registration_key_additional1:
                inv_dict["FacturaRecibida"].update(
                    {
                        "ClaveRegimenEspecialOTrascendenciaAdicional1": (
                            self.sii_registration_key_additional1.code
                        )
                    }
                )
            if self.sii_registration_key_additional2:
                inv_dict["FacturaRecibida"].update(
                    {
                        "ClaveRegimenEspecialOTrascendenciaAdicional2": (
                            self.sii_registration_key_additional2.code
                        )
                    }
                )
            # Uso condicional de IDOtro/NIF
            inv_dict["FacturaRecibida"]["Contraparte"].update(ident)
            if self.move_type == "in_refund":
                rec_dict = inv_dict["FacturaRecibida"]
                rec_dict["TipoRectificativa"] = self.sii_refund_type
                if self.sii_refund_type == "S":
                    refund_tax_amount = self.refund_invoice_id._get_sii_in_taxes()[1]
                    rec_dict["ImporteRectificacion"] = {
                        "BaseRectificada": abs(
                            self.refund_invoice_id.amount_untaxed_signed
                        ),
                        "CuotaRectificada": refund_tax_amount,
                    }
        return inv_dict

    def _get_cancel_sii_invoice_dict(self):
        self.ensure_one()
        self._aeat_check_exceptions()
        if self.move_type in ["out_invoice", "out_refund"]:
            return self._get_aeat_invoice_dict_out(cancel=True)
        elif self.move_type in ["in_invoice", "in_refund"]:
            return self._get_aeat_invoice_dict_in(cancel=True)
        return {}

    def _sii_invoice_dict_not_modified(self):
        self.ensure_one()
        to_send = self._get_aeat_invoice_dict()
        content_sent = json.loads(self.aeat_content_sent)
        return to_send == content_sent

    def _post(self, soft=True):
        res = super()._post(soft=soft)
        for invoice in self.filtered(lambda x: x.sii_enabled and x.is_invoice()):
            invoice._aeat_check_exceptions()
            if (
                invoice.aeat_state in ["sent_modified", "sent"]
                and invoice._sii_invoice_dict_not_modified()
            ):
                if invoice.aeat_state == "sent_modified":
                    invoice.aeat_state = "sent"
                continue
            if invoice.aeat_state == "sent":
                invoice.aeat_state = "sent_modified"
            elif invoice.aeat_state == "cancelled":
                invoice.aeat_state = "cancelled_modified"
            company = invoice.company_id
            if company.sii_method != "auto":
                continue
            invoice._process_sii_send()
        return res

    def process_send_sii(self):
        return {
            "name": "Confirmation message for sending invoices to the SII",
            "type": "ir.actions.act_window",
            "view_mode": "form",
            "res_model": "wizard.send.sii",
            "views": [(False, "form")],
            "target": "new",
            "context": self.env.context,
        }

    def _get_sii_jobs_field_name(self):
        return "invoice_jobs_ids"

    def _get_valid_document_states(self):
        return SII_VALID_INVOICE_STATES

    def _cancel_invoice_to_sii(self):
        for invoice in self.filtered(lambda i: i.state in ["cancel"]):
            serv = invoice._connect_aeat(invoice.move_type)
            header = invoice._get_aeat_header(cancellation=True)
            inv_vals = {
                "aeat_send_failed": True,
                "aeat_send_error": False,
            }
            try:
                inv_dict = invoice._get_cancel_sii_invoice_dict()
                if invoice.move_type in ["out_invoice", "out_refund"]:
                    res = serv.AnulacionLRFacturasEmitidas(header, inv_dict)
                else:
                    res = serv.AnulacionLRFacturasRecibidas(header, inv_dict)
                # TODO Facturas intracomunitarias 66 RIVA
                # elif invoice.fiscal_position_id.id == self.env.ref(
                #     'account.fp_intra').id:
                #     res = serv.AnulacionLRDetOperacionIntracomunitaria(
                #         header, invoices)
                inv_vals["sii_return"] = res
                if res["EstadoEnvio"] == "Correcto":
                    inv_vals.update(
                        {
                            "aeat_state": "cancelled",
                            "sii_csv": res["CSV"],
                            "aeat_send_failed": False,
                        }
                    )
                res_line = res["RespuestaLinea"][0]
                if res_line["CodigoErrorRegistro"]:
                    inv_vals["aeat_send_error"] = "{} | {}".format(
                        str(res_line["CodigoErrorRegistro"]),
                        str(res_line["DescripcionErrorRegistro"])[:60],
                    )
                invoice.write(inv_vals)
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                invoice = env["account.move"].browse(invoice.id)
                inv_vals.update(
                    {
                        "aeat_send_failed": True,
                        "aeat_send_error": repr(fault)[:60],
                        "sii_return": repr(fault),
                    }
                )
                invoice.write(inv_vals)
                new_cr.commit()
                new_cr.close()
                raise

    def cancel_sii(self):
        invoices = self.filtered(
            lambda i: (
                i.sii_enabled
                and i.state in ["cancel"]
                and i.aeat_state in ["sent", "sent_w_errors", "sent_modified"]
            )
        )
        if not invoices._cancel_sii_jobs():
            raise exceptions.UserError(
                _(
                    "You can not communicate the cancellation of this invoice "
                    "at this moment because there is a job running!"
                )
            )
        queue_obj = self.env["queue.job"]
        for invoice in invoices:
            company = invoice.company_id
            if not company.use_connector:
                invoice._cancel_invoice_to_sii()
            else:
                eta = company._get_sii_eta()
                new_delay = (
                    self.sudo()
                    .with_context(company_id=company.id)
                    .with_delay(eta=eta)
                    .cancel_one_invoice()
                )
                job = queue_obj.search([("uuid", "=", new_delay.uuid)], limit=1)
                invoice.sudo().invoice_jobs_ids |= job

    def button_cancel(self):
        if not self._cancel_sii_jobs():
            raise exceptions.UserError(
                _("You can not cancel this invoice because" " there is a job running!")
            )
        res = super().button_cancel()
        for invoice in self.filtered(lambda x: x.sii_enabled):
            if invoice.aeat_state == "sent":
                invoice.aeat_state = "sent_modified"
            elif invoice.aeat_state == "cancelled_modified":
                # Case when repoen a cancelled invoice, validate and cancel
                # again without any SII communication.
                invoice.aeat_state = "cancelled"
        return res

    def button_draft(self):
        if not self._cancel_sii_jobs():
            raise exceptions.UserError(
                _(
                    "You can not set to draft this invoice because"
                    " there is a job running!"
                )
            )
        return super().button_draft()

    def _get_document_product_exempt(self, applied_taxes):
        return set(
            self.mapped("invoice_line_ids")
            .filtered(
                lambda x: (
                    any(tax in x.tax_ids for tax in applied_taxes)
                    and x.product_id.sii_exempt_cause
                    and x.product_id.sii_exempt_cause != "none"
                )
            )
            .mapped("product_id.sii_exempt_cause")
        )

    def is_sii_invoice(self):
        """Hook method to be overridden in additional modules to verify
        if the invoice must be sended trough SII system, for special cases.

        :param self: Single invoice record
        :return: bool value indicating if the invoice should be sent to SII.
        """
        self.ensure_one()

    @api.depends(
        "invoice_line_ids",
        "invoice_line_ids.name",
        "company_id",
    )
    def _compute_sii_description(self):
        default_description = self.default_get(["sii_description"])["sii_description"]
        for invoice in self:
            description = ""
            if invoice.move_type in ["out_invoice", "out_refund"]:
                description = invoice.company_id.sii_header_customer or ""
            elif invoice.move_type in ["in_invoice", "in_refund"]:
                description = invoice.company_id.sii_header_supplier or ""
            method = invoice.company_id.sii_description_method
            if method == "fixed":
                description = (
                    description + invoice.company_id.sii_description
                ) or default_description
            elif method == "manual":
                if invoice.sii_description != default_description:
                    # keep current content if not default
                    description = invoice.sii_description
            else:  # auto method
                if invoice.invoice_line_ids:
                    if description:
                        description += " | "
                    names = invoice.mapped("invoice_line_ids.name") or invoice.mapped(
                        "invoice_line_ids.ref"
                    )
                    description += " - ".join(filter(None, names))
            invoice.sii_description = (description or "")[:500] or "/"

    @api.depends(
        "company_id",
        "company_id.sii_enabled",
        "move_type",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
    )
    def _compute_sii_enabled(self):
        """Compute if the invoice is enabled for the SII"""
        for invoice in self:
            if invoice.company_id.sii_enabled and invoice.is_invoice():
                invoice.sii_enabled = (
                    invoice.fiscal_position_id
                    and invoice.fiscal_position_id.aeat_active
                ) or not invoice.fiscal_position_id
            else:
                invoice.sii_enabled = False

    def _reverse_moves(self, default_values_list=None, cancel=False):
        # OVERRIDE
        if not default_values_list:
            default_values_list = [{} for move in self]
        for move, default_values in zip(self, default_values_list):
            if move.sii_enabled:
                extra_dict = {}
                sii_refund_type = self.env.context.get("sii_refund_type", False)
                supplier_invoice_number_refund = move.env.context.get(
                    "supplier_invoice_number", False
                )
                if sii_refund_type:
                    extra_dict["sii_refund_type"] = sii_refund_type
                if supplier_invoice_number_refund:
                    extra_dict["ref"] = supplier_invoice_number_refund
                if extra_dict:
                    default_values.update(extra_dict)
        res = super()._reverse_moves(
            default_values_list=default_values_list,
            cancel=cancel,
        )
        return res

    def cancel_one_invoice(self):
        self.sudo()._cancel_invoice_to_sii()
