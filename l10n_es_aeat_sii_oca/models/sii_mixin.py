# Copyright 2021 Tecnativa - João Marques
# Copyright 2022 ForgeFlow - Lois Rilo
# Copyright 2023 Aures Tic - Almudena de la Puente <almudena@aurestic.es>
# Copyright 2023 Aures Tic - Jose Zambudio <jose@aurestic.es>
# Copyright 2011,2024 Tecnativa - Pedro M. Baeza
# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import json
from pprint import pformat

from unidecode import unidecode

from odoo import api, exceptions, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain
from odoo.modules.registry import Registry
from odoo.tools.float_utils import float_compare

from odoo.addons.l10n_es_aeat.models.aeat_mixin import round_by_keys

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
    )
    sii_description = fields.Char(
        string="SII computed description",
        compute="_compute_sii_description",
        size=500,
        default="/",
        store=True,
        readonly=False,
        copy=False,
    )
    aeat_state = fields.Selection(
        selection_add=SII_STATES,
    )
    sii_csv = fields.Char(string="SII CSV", copy=False, readonly=True, index=True)
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
    sii_enabled = fields.Boolean(
        string="Enable SII",
        compute="_compute_sii_enabled",
        search="_search_sii_enabled",
    )
    sii_macrodata = fields.Boolean(
        string="MacroData",
        help="Check to confirm that the document has an absolute amount "
        "greater o equal to 100 000 000,00 euros.",
        compute="_compute_macrodata",
    )
    sii_send_date = fields.Datetime(string="SII Send Date", index=True, copy=False)
    sii_needs_cancel = fields.Boolean(readonly=True, copy=False)

    def _compute_sii_refund_type(self):
        self.sii_refund_type = False

    def _compute_sii_description(self):
        self.sii_description = "/"

    def _compute_sii_enabled(self):
        raise NotImplementedError

    @api.model
    def _is_unsupported_search_operator(self, operator):
        return operator not in ("in", "not in")

    @api.model
    def _search_sii_enabled(self, operator, value):
        if self._is_unsupported_search_operator(operator):
            raise ValueError(self.env._("Unsupported search operator"))
        return Domain("company_id.sii_enabled", operator, value)

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
        that are not in not_sent sii status or False."""
        return self.filtered(lambda rec: rec.aeat_state not in ["not_sent", False])

    @api.ondelete(at_uninstall=False)
    def _unlink_except_sii(self):
        """Do not allow the deletion of records already sent to the SII."""
        if self._filter_sii_unlink_not_possible():
            raise exceptions.UserError(
                self.env._(
                    "You cannot delete an invoice already registered at the SII."
                )
            )

    def _get_sii_document_taxes(self):
        """Return the taxes (group taxes flattened) of the document."""
        raise NotImplementedError()

    def _get_sii_tax_scope(self, tax):
        """Return 'service' or 'consu' for placing the tax in the services or the
        goods block of the breakdown."""
        return "service" if tax.tax_scope == "service" else "consu"

    @api.model
    def _get_sii_fiscal_position_gen_type(self, fiscal_position):
        """Return 1 (national), 2 (intra-community) or 3 (export) for a fiscal
        position."""
        partner_ident = fiscal_position.sii_partner_identification_type
        if partner_ident:
            return int(partner_ident)
        if fiscal_position.name == "Régimen Intracomunitario":
            return 2
        if fiscal_position.name == "Régimen Extracomunitario":
            return 3
        return 1

    def _is_sii_self_assessed_tax(self, tax):
        """Purchase tax self-assessed on an intra-community or foreign operation,
        whose quota the AEAT expects in ImporteTotal (it is not in the invoice
        total, as its negative repartition line cancels it). The operation is
        foreign when the invoice is, or when the tax only belongs to
        intra-community or foreign fiscal positions; national reverse charge is
        not added."""
        if not any(
            line.repartition_type == "tax" and line.factor_percent < 0
            for line in tax.invoice_repartition_line_ids
        ):
            return False
        if self._get_sii_gen_type() in (2, 3):
            return True
        positions = tax.fiscal_position_ids
        return bool(positions) and all(
            self._get_sii_fiscal_position_gen_type(position) in (2, 3)
            for position in positions
        )

    def _get_sii_tax_codes(self, tax):
        """Return the SII breakdown codes of a tax of the document, from the
        Spanish data of the tax (type, scope and investment good):

        * Sales: SFESB/SFESS (subject, goods/services), SFESISP (reverse
          charge), SFESBE/SFESSE (exempt, goods/services) and SFENS/SFESNS (not
          subject, goods/services).
        * Purchases: SFRS (subject, exempt and DUA), SFRSA (REAGYP), SFRISP
          (reverse charge), SFRNS (not subject), SFRND (not deductible), SFRBI
          (investment good) and NotIncludedInTotalNegative (self-assessed VAT
          of a foreign invoice).
        * Both: RE (equivalence surcharge) and NotIncludedInTotal (withholding,
          or any tax whose quota is not in the invoice total).

        Taxes of type 'ignore' get no code: they are not reported, as the taxes
        that are not for the tax agency of the document (see
        `_is_sii_reported_tax`).
        """
        if not self._is_sii_reported_tax(tax):
            return set()
        es_type = tax.l10n_es_type
        if es_type == "recargo":
            return {"RE"}
        if es_type == "retencion":
            return {"NotIncludedInTotal"}
        codes = set()
        if self._get_mapping_key() in ("out_invoice", "out_refund"):
            is_service = self._get_sii_tax_scope(tax) == "service"
            if es_type == "sujeto":
                codes.add("SFESS" if is_service else "SFESB")
            elif es_type == "sujeto_isp":
                codes.add("SFESISP")
            elif es_type == "exento":
                codes.add("SFESSE" if is_service else "SFESBE")
            elif es_type in ("no_sujeto", "no_sujeto_loc"):
                codes.add("SFESNS" if is_service else "SFENS")
            return codes
        if es_type in ("sujeto", "exento", "dua"):
            codes.add("SFRS")
        elif es_type == "sujeto_agricultura":
            codes.add("SFRSA")
        elif es_type == "sujeto_isp":
            codes.add("SFRISP")
        elif es_type in ("no_sujeto", "no_sujeto_loc"):
            codes.add("SFRNS")
        elif es_type == "no_deducible":
            codes.add("SFRND")
        if codes and tax.l10n_es_bien_inversion:
            codes.add("SFRBI")
        if codes and self._is_sii_self_assessed_tax(tax):
            codes.add("NotIncludedInTotalNegative")
        return codes

    def _is_sii_reported_tax(self, tax):
        """The SII of the AEAT is for the VAT: the taxes of other indirect taxes
        (IGIC, IPSI) are not reported to it. Taxes without applicability, such
        as withholdings or equivalence surcharges, are."""
        return tax.l10n_es_applicability in (False, "01")

    def _get_aeat_taxes_map(self, codes, date):
        """Return the taxes of the document that go to the given SII breakdown
        codes (see `_get_sii_tax_codes`).

        :param codes: List of code strings to get the taxes.
        :param date: Unused, kept for the API of `aeat.mixin`.
        :return: Recordset with the corresponding taxes
        """
        codes = set(codes)
        return self._get_sii_document_taxes().filtered(
            lambda tax: self._get_sii_tax_codes(tax) & codes
        )

    def _get_sii_amount_not_in_total(self, tax_line, codes):
        """Return the amount of a tax line that is not in ImporteTotal:
        withholdings, foreign VAT of not subject operations (OSS) and, with a
        negative sign, self-assessed VAT of foreign invoices."""
        if "NotIncludedInTotal" in codes:
            return tax_line["amount"]
        if "NotIncludedInTotalNegative" in codes:
            return -tax_line["amount"]
        if codes and tax_line["tax"].l10n_es_type in ("no_sujeto", "no_sujeto_loc"):
            return tax_line["amount"]
        return 0

    def _get_sii_base_not_in_total(self):
        """Return the base of the operations that are outside the invoice for VAT
        purposes (lines whose taxes are all of type 'ignore', e.g.
        disbursements), which is not in ImporteTotal."""
        return 0

    def _get_dua_sii_exempt_taxes(self):
        self.ensure_one()
        return self.company_id._get_taxes_from_xmlids(
            ["account_tax_template_p_dua_exempt"]
        )

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
                self.env._(
                    "No VAT configured for the company '%s'", self.company_id.name
                )
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

    def _cancel_send_to_sii(self):
        if not any(self.sudo().mapped("sii_send_date")):
            return True
        try:
            self.sudo().write({"sii_send_date": False})
        except Exception:  # noqa: BLE001
            return False
        return True

    def _sii_filter_to_send(self):
        """Helper method to filter documents to send to SII."""
        return self.filtered(lambda document: document._is_sii_document_to_send())

    def _is_sii_document_to_send(self):
        self.ensure_one()
        if not self.sii_enabled:
            return False
        if self.sii_needs_cancel:
            return self.state == "cancel" and self.aeat_state in [
                "sent",
                "sent_w_errors",
                "sent_modified",
            ]
        return (
            self.state in self._get_valid_document_states()
            and self.aeat_state not in ["sent", "cancelled"]
        )

    def send_sii_now(self):
        documents = self._sii_filter_to_send()
        if documents:
            documents._process_sii_send(send_date=fields.Datetime.now())

    def send_sii(self):
        documents = self._sii_filter_to_send()
        if not documents._cancel_send_to_sii():
            raise UserError(
                self.env._(
                    "You can not communicate this document at this moment. "
                    "Please, try again later."
                )
            )
        if documents:
            documents._process_sii_send()

    def _process_sii_send(self, send_date=None):
        """Process document sending to the SII. Adds general checks from
        configuration parameters and document availability for SII."""
        if send_date:
            self.sii_send_date = send_date
        else:
            for record in self:
                # If the document failed to be sent to SII previously, send it now
                if record.aeat_send_failed:
                    record.sii_send_date = fields.Datetime.now()
                else:
                    record.sii_send_date = record.company_id._get_sii_sending_time()
        # Create trigger if any company needs to send doc to SII now
        # so the sending to SII cron is executed as soon as possible
        if (
            self.company_id.filtered(
                lambda company: (
                    company.send_mode == "auto"
                    or (company.send_mode == "delayed" and company.delay_time == 0.0)
                )
            )
            or send_date
        ):
            self.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")._trigger()

    def _bind_service(self, client, port_name, address=None):
        self.ensure_one()
        service = client._get_service("siiService")
        port = client._get_port(service, port_name)
        address = address or port.binding_options["address"]
        return client.create_service(port.binding.name, address)

    def _get_sii_tax_agency(self):
        return self.company_id.tax_agency_id

    def _connect_params_aeat(self, mapping_key):
        self.ensure_one()
        agency = self._get_sii_tax_agency()
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
        return self._get_sii_fiscal_position_gen_type(self.fiscal_position_id)

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
                and not partner._has_valid_aeat_identification()
                and not is_simplified_invoice
            ):
                raise UserError(self.env._("The partner has not a VAT configured."))
            if not self.sii_enabled:
                raise UserError(self.env._("This invoice is not SII enabled."))
        return res

    def _get_document_fiscal_date(self):
        raise NotImplementedError()

    def _get_document_fiscal_year(self):
        return fields.Date.to_date(self._get_document_fiscal_date()).year

    def _get_document_period(self):
        month = fields.Date.to_date(self._get_document_fiscal_date()).month
        if self.company_id.sii_period == "monthly":
            period = f"{month:02d}"
        else:
            period = str(int(((month - 1) / 3) + 1)) + "T"
        return period

    def _get_sii_exempt_cause(self, tax):
        """Return the exemption cause (CausaExencion) of an exempt tax: the one
        of the tax, else E5 on intra-community operations and E2 on exports, as
        the cause is optional for the AEAT."""
        if tax.l10n_es_exempt_reason:
            return tax.l10n_es_exempt_reason
        return {2: "E5", 3: "E2"}.get(self._get_sii_gen_type(), False)

    def _add_sii_exempt_detail(self, breakdown, tax, base):
        """Add the base of an exempt tax to its exemption cause detail."""
        exempt_dict = breakdown.setdefault("Sujeta", {}).setdefault(
            "Exenta", {"DetalleExenta": []}
        )
        exempt_cause = self._get_sii_exempt_cause(tax)
        for detail in exempt_dict["DetalleExenta"]:
            if detail.get("CausaExencion") == exempt_cause:
                detail["BaseImponible"] += base
                return
        detail = {"BaseImponible": base}
        if exempt_cause:
            detail["CausaExencion"] = exempt_cause
        exempt_dict["DetalleExenta"].append(detail)

    def _get_tax_info(self):
        # TODO: To be renamed to _get_sii_tax_info
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

    def _get_sii_no_taxable_cause(self, tax):
        """Return the NoSujeta node of a not subject tax: articles 7, 14 and
        others, or location rules."""
        if tax.l10n_es_type == "no_sujeto":
            return "ImportePorArticulos7_14_Otros"
        return "ImporteTAIReglasLocalizacion"

    def _get_sii_regime_codes(self):
        """Return the AEAT registration keys of the document: main first, then
        the additional ones."""
        raise NotImplementedError()

    @api.model
    def _merge_tax_dict(self, vat_list, tax_dict, comp_keys, merge_keys):
        """Helper method for merging values in an existing tax dictionary.

        :param vat_list: List of tax dictionaries to check for merge.
        :param tax_dict: Tax dictionary to merge.
        :param comp_keys: List of keys to compare for matching.
        :param merge_keys: List of keys whose values should be summed.
        """
        for existing_dict in vat_list:
            match = True
            for key in comp_keys:
                if existing_dict.get(key, "-99") != tax_dict.get(key, "-99"):
                    match = False
                    break
            if match:
                for key in merge_keys:
                    existing_dict[key] += tax_dict[key]
                return True
        return False

    def _is_sii_type_breakdown_required(self):
        """Calculates if the block 'DesgloseTipoOperacion' is required for
        the invoice communication."""
        self.ensure_one()
        sii_gen_type = self._get_sii_gen_type()
        if sii_gen_type in (2, 3):
            # DesgloseTipoOperacion required for Intracommunity and
            # Export operations
            return True
        elif sii_gen_type == 1 and not self._is_aeat_simplified_invoice():
            identifier = self._get_sii_identifier()
            if "IDOtro" in identifier:
                # DesgloseTipoOperacion required for national operations
                # with 'IDOtro' in the SII identifier block
                return True
            elif identifier.get("NIF", "").startswith("N"):
                # DesgloseTipoOperacion required if customer's country is Spain and
                # has a NIF which starts with 'N'
                return True
        return False

    def _get_sii_out_taxes(self):
        """Get the taxes for sales documents.

        :param self: Single document record.
        """
        self.ensure_one()
        taxes_dict = {}
        do_breakdown = self._is_sii_type_breakdown_required()
        if do_breakdown:
            tax_breakdown = taxes_dict.setdefault("DesgloseTipoOperacion", {})
            good_breakdown = tax_breakdown.setdefault("Entrega", {})
            service_breakdown = tax_breakdown.setdefault("PrestacionServicios", {})
        else:
            tax_breakdown = taxes_dict.setdefault("DesgloseFactura", {})
            good_breakdown = tax_breakdown
            service_breakdown = tax_breakdown
        not_in_amount_total = self._get_sii_base_not_in_total()
        tax_lines = self._get_tax_info()
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            codes = self._get_sii_tax_codes(tax)
            not_in_amount_total += self._get_sii_amount_not_in_total(tax_line, codes)
            if codes & {"SFESBE", "SFESSE"}:
                breakdown = good_breakdown if "SFESBE" in codes else service_breakdown
                self._add_sii_exempt_detail(breakdown, tax, tax_line["base"])
            elif codes & {"SFESB", "SFESISP", "SFESS"}:
                breakdown = service_breakdown if "SFESS" in codes else good_breakdown
                # TODO: services with reverse charge (S2) are sent as S1
                not_exempt_type = "S2" if "SFESISP" in codes else "S1"
                sub_dict = breakdown.setdefault("Sujeta", {})
                sub_dict.setdefault(
                    "NoExenta",
                    {
                        "TipoNoExenta": not_exempt_type,
                        "DesgloseIVA": {"DetalleIVA": []},
                    },
                )
                if not_exempt_type != sub_dict["NoExenta"]["TipoNoExenta"]:
                    # There's a mix of ISP/non ISP -> S3
                    sub_dict["NoExenta"]["TipoNoExenta"] = "S3"
                sub = sub_dict["NoExenta"]["DesgloseIVA"]["DetalleIVA"]
                tax_dict = self._get_sii_tax_dict(tax_line, tax_lines)
                if not self._merge_tax_dict(
                    sub,
                    tax_dict,
                    ["TipoImpositivo"],
                    ["BaseImponible", "CuotaRepercutida"],
                ):
                    sub.append(tax_dict)
            elif codes & {"SFENS", "SFESNS"}:
                breakdown = service_breakdown if "SFESNS" in codes else good_breakdown
                no_taxable_cause = self._get_sii_no_taxable_cause(tax)
                nsub_dict = breakdown.setdefault("NoSujeta", {})
                nsub_dict.setdefault(no_taxable_cause, 0)
                nsub_dict[no_taxable_cause] += tax_line["base"]
        # Ajustes finales breakdown: eliminar clave vacía de entrega / servicios
        if "DesgloseTipoOperacion" in taxes_dict:
            if not taxes_dict["DesgloseTipoOperacion"]["Entrega"]:
                del taxes_dict["DesgloseTipoOperacion"]["Entrega"]
            if not taxes_dict["DesgloseTipoOperacion"]["PrestacionServicios"]:
                del taxes_dict["DesgloseTipoOperacion"]["PrestacionServicios"]
        return taxes_dict, not_in_amount_total

    def _get_sii_invoice_type(self):
        raise NotImplementedError()

    def _get_sii_identifier(self):
        """Get the SII structure for a partner identifier depending on the
        conditions of the invoice.
        """
        self.ensure_one()
        gen_type = self._get_sii_gen_type()
        partner = self._aeat_get_partner()
        (
            country_code,
            identifier_type,
            identifier,
        ) = partner._parse_aeat_vat_info()
        # Preserve the VAT country prefix when it is explicitly set, even if it
        # differs from the partner's address country.
        if partner.vat and len(partner.vat) > 1 and partner.vat[1].isalpha():
            vat_prefix = partner.vat[:2].upper()
            country = self.env["res.country"].search(
                [("code", "=", vat_prefix)], limit=1
            )
        else:
            vat_prefix = country_code
            country = partner.country_id
        # Map it, as the AEAT expects some prefixes different from the ISO
        # code (e.g. EL for Greece instead of GR)
        vat_country_code = partner._map_aeat_country_iso_code(country) or vat_prefix
        # Limpiar alfanum
        if identifier:
            identifier = "".join(e for e in identifier if e.isalnum()).upper()
        else:
            identifier = "NO_DISPONIBLE"
            identifier_type = "06"
        full_eu_vat = identifier
        if (
            partner._map_aeat_country_code(vat_country_code)
            in partner._get_aeat_europe_codes()
        ):
            full_eu_vat = (
                identifier
                if identifier.startswith(vat_country_code)
                else vat_country_code + identifier
            )
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
                        # Only a VAT number carries the country prefix, not a
                        # passport or another identification document
                        "ID": full_eu_vat if identifier_type == "02" else identifier,
                    },
                }
        elif gen_type == 2:
            if identifier_type == "02":
                return {"IDOtro": {"IDType": "02", "ID": full_eu_vat}}
            if identifier_type:
                return {
                    "IDOtro": {
                        "CodigoPais": country_code,
                        "IDType": identifier_type,
                        "ID": identifier,
                    },
                }
            return {"NIF": identifier}
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
            regime_codes = self._get_sii_regime_codes()
            inv_dict["FacturaExpedida"] = {
                "TipoFactura": self._get_sii_invoice_type(),
                "ClaveRegimenEspecialOTrascendencia": regime_codes[0],
                "DescripcionOperacion": self.sii_description,
                "TipoDesglose": tipo_desglose,
                "ImporteTotal": amount_total,
            }
            for index, regime_code in enumerate(regime_codes[1:], start=1):
                inv_dict["FacturaExpedida"][
                    f"ClaveRegimenEspecialOTrascendenciaAdicional{index}"
                ] = regime_code
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

    def _send_document_to_sii(self):  # noqa: C901
        documents = self.filtered(
            lambda i: i.state in self._get_valid_document_states()
        )
        headers = {}
        grouped_data = {
            "not_sent": {
                "in": {"payload": {}, "documents": {}, "docs_vals": {}},
                "out": {"payload": {}, "documents": {}, "docs_vals": {}},
            },
            "others": {
                "in": {"payload": {}, "documents": {}, "docs_vals": {}},
                "out": {"payload": {}, "documents": {}, "docs_vals": {}},
            },
        }
        documents_not_sent = documents.filtered(lambda r: r.aeat_state == "not_sent")
        other_documents = documents - documents_not_sent
        if documents_not_sent:
            headers.update(
                {"not_sent": fields.first(documents_not_sent)._get_aeat_header("A0")}
            )
        if other_documents:
            headers.update(
                {"others": fields.first(other_documents)._get_aeat_header("A1")}
            )
        # Prepare grouped data to send and vals to update document record
        for document in documents:
            # Filter the SII description for avoiding manual invalid inputs
            text = unidecode(document.sii_description)
            if text != document.sii_description:
                document.sii_description = text
            if document.aeat_state == "not_sent":
                doc_vals = {
                    "aeat_header_sent": json.dumps(headers["not_sent"], indent=4),
                }
            else:
                doc_vals = {
                    "aeat_header_sent": json.dumps(headers["others"], indent=4),
                }
            inv_dict = False
            try:
                inv_dict = document._get_aeat_invoice_dict()
                mapping_key = document._get_mapping_key()
                doc_vals["aeat_content_sent"] = json.dumps(inv_dict, indent=4)
                communication_type = (
                    "others"
                    if document.aeat_state != "not_sent"
                    else document.aeat_state
                )
                docs_group = grouped_data[communication_type]
                if mapping_key in ["out_invoice", "out_refund"]:
                    invoice_type = "out"
                if mapping_key in ["in_invoice", "in_refund"]:
                    invoice_type = "in"
                docs_group[invoice_type]["payload"].update({document.id: inv_dict})
                docs_group[invoice_type]["documents"].update(
                    {document._get_document_serial_number(): document}
                )
                docs_group[invoice_type]["docs_vals"].update({document.id: doc_vals})
            except Exception as fault:
                new_cr = Registry(self.env.cr.dbname).cursor()
                env = api.Environment(new_cr, self.env.uid, self.env.context)
                document = env[document._name].browse(document.id)
                doc_vals.update(
                    {
                        "aeat_send_failed": True,
                        "aeat_send_error": repr(fault)[:60],
                        "sii_return": repr(fault),
                        "sii_send_date": False,
                    }
                )
                if inv_dict:
                    doc_vals["aeat_content_sent"] = json.dumps(inv_dict, indent=4)
                document.write(doc_vals)
                new_cr.commit()
                new_cr.close()
        # Start send documents to the AEAT
        for status in ("not_sent", "others"):
            header = headers.get(status)
            if not header:
                continue
            docs_group = grouped_data.get(status)
            for invoice_type in ("out", "in"):
                payload = list(docs_group.get(invoice_type)["payload"].values())
                if not payload:
                    continue
                first_document = list(
                    docs_group.get(invoice_type)["documents"].values()
                )[0]
                try:
                    serv = first_document._connect_aeat(
                        first_document._get_mapping_key()
                    )
                    if invoice_type == "out":
                        res = serv.SuministroLRFacturasEmitidas(header, payload)
                    else:
                        res = serv.SuministroLRFacturasRecibidas(header, payload)
                    # TODO Facturas intracomunitarias 66 RIVA
                    # elif invoice.fiscal_position_id.id == self.env.ref(
                    #     'account.fp_intra').id:
                    #     res = serv.SuministroLRDetOperacionIntracomunitaria(
                    #         header, invoices)
                except Exception as fault:
                    new_cr = Registry(self.env.cr.dbname).cursor()
                    env = api.Environment(new_cr, self.env.uid, self.env.context)
                    doc_ids = list(docs_group[invoice_type]["docs_vals"].keys())
                    docs_vals = docs_group[invoice_type]["docs_vals"]
                    document_ids = env[first_document._name].browse(doc_ids)
                    for document in document_ids:
                        doc_vals = docs_vals.get(document.id, {})
                        doc_vals.update(
                            {
                                "aeat_send_failed": True,
                                "aeat_send_error": repr(fault)[:60],
                                "sii_return": repr(fault),
                                "sii_send_date": False,
                            }
                        )
                        document.write(doc_vals)
                    new_cr.commit()
                    new_cr.close()
                    continue
                sii_returned_shared_data = {
                    "DatosPresentacion": res["DatosPresentacion"],
                    "Cabecera": res["Cabecera"],
                    "EstadoEnvio": res["EstadoEnvio"],
                }
                for res_line in res["RespuestaLinea"]:
                    csv = res.get("CSV") or res_line.get("CSV")
                    res_line_state = res_line.get("EstadoRegistro")
                    # Search invoice record
                    document = docs_group.get(invoice_type)["documents"].get(
                        res_line["IDFactura"]["NumSerieFacturaEmisor"], None
                    )
                    # Search invoice vals
                    if not document:
                        continue
                    doc_vals = docs_group.get(invoice_type)["docs_vals"].get(
                        document.id, None
                    )
                    if doc_vals is None:
                        continue
                    if res_line_state == "Correcto":
                        doc_vals.update(
                            {
                                "aeat_state": "sent",
                                "sii_csv": csv,
                                "aeat_send_failed": False,
                            }
                        )
                    elif res_line_state == "AceptadoConErrores":
                        doc_vals.update(
                            {
                                "aeat_state": "sent_w_errors",
                                "sii_csv": csv,
                                "aeat_send_failed": True,
                            }
                        )
                    else:
                        doc_vals["aeat_send_failed"] = True
                    if (
                        "aeat_state" in doc_vals
                        and not document.sii_account_registration_date
                        and invoice_type == "in"
                    ):
                        doc_vals["sii_account_registration_date"] = (
                            document._get_account_registration_date()
                        )
                    doc_vals["sii_return"] = pformat(
                        {
                            **sii_returned_shared_data,
                            "CSV": csv,
                            "RespuestaLinea": [res_line],
                        },
                        width=120,
                        sort_dicts=False,
                    )
                    doc_vals["sii_send_date"] = False
                    send_error = False
                    if res_line["CodigoErrorRegistro"]:
                        send_error = "{} | {}".format(
                            str(res_line["CodigoErrorRegistro"]),
                            str(res_line["DescripcionErrorRegistro"])[:60],
                        )
                    doc_vals["aeat_send_error"] = send_error
                    document.write(doc_vals)

    def confirm_one_document(self):
        self.sudo()._send_document_to_sii()
