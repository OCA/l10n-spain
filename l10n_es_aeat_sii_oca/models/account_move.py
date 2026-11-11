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

from unidecode import unidecode

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.fields import Domain

SII_VALID_INVOICE_STATES = ["posted"]
# Types allowed with the marks of art. 7.2/7.3 and of art. 6.1.d RD 1619/2012
# (AEAT errors 2022 and 2023; F3 is not a type of Odoo core)
SII_QUALIFIED_SIMPLIFIED_TYPES = ("F1", "R1", "R2", "R3", "R4")
SII_UNIDENTIFIED_RECIPIENT_TYPES = ("F2", "R5")
# AEAT limit of simplified invoices (art. 4.2 RD 1619/2012, validation 20)
SII_SIMPLIFIED_INVOICE_LIMIT = 3000
_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "sii.mixin"]  # noqa: RUF012

    def _get_default_type(self):
        context = self.env.context
        return context.get("move_type", context.get("default_move_type"))

    def _default_sii_refund_type(self):
        inv_type = self._get_default_type()
        return "I" if inv_type in ["out_refund", "in_refund"] else False

    l10n_es_regime_code_additional2 = fields.Selection(
        string="VAT Regime Code (Additional 2)",
        selection="_l10n_es_regime_code_selection",
        compute="_compute_l10n_es_regime_code",
        store=True,
        readonly=False,
    )
    sii_property_location = fields.Selection(
        string="Real property location",
        copy=False,
        selection=[
            (
                "1",
                (
                    "[1]-Real property with cadastral code located within "
                    "the Spanish territory except Basque Country or Navarra"
                ),
            ),
            ("2", "[2]-Real property located in the Basque Country or Navarra"),
            (
                "3",
                (
                    "[3]-Real property in any of the above situations "
                    "but without cadastral code"
                ),
            ),
            ("4", "[4]-Real property located in a foreign country"),
        ],
    )
    sii_property_cadastrial_code = fields.Char(
        string="Real property cadastrial code",
        copy=False,
    )
    sii_property_required = fields.Boolean(compute="_compute_sii_property_required")
    sii_dua_invoice = fields.Boolean(compute="_compute_dua_invoice")
    sii_qualified_simplified_invoice = fields.Boolean(
        string="Qualified simplified invoice",
        compute="_compute_sii_invoice_marks",
        store=True,
        readonly=False,
        copy=False,
        help="Simplified invoice that identifies the recipient, as art. 7.2 and "
        "7.3 RD 1619/2012 allow when the recipient asks for it (F1 or R1-R4). "
        "Set on the customer invoices of a simplified invoices journal; on a "
        "vendor bill, check it when the supplier issued a simplified invoice "
        "with your company's VAT number.",
    )
    sii_unidentified_recipient_invoice = fields.Boolean(
        string="Invoice without recipient identification (art. 6.1.d)",
        compute="_compute_sii_invoice_marks",
        store=True,
        readonly=False,
        copy=False,
        help="Full invoice without the recipient's VAT number, which art. 6.1.d "
        "RD 1619/2012 only requires for intra-community deliveries, reverse "
        "charge and operations located in Spain (F2 or R5). Set on the "
        "simplified type invoices of a full invoices journal whose taxes are all "
        "not subject by location rules, such as distance sales to consumers of "
        "other member states. Unlike simplified invoices, it has no amount limit.",
    )
    sii_send_date_visible = fields.Boolean(compute="_compute_sii_send_date_visible")

    @api.depends("move_type")
    def _compute_sii_refund_type(self):
        for record in self:
            if "refund" in (record.move_type or ""):
                record.sii_refund_type = "I"
            else:
                record.sii_refund_type = False

    @api.depends("commercial_partner_id.aeat_simplified_invoice")
    def _compute_l10n_es_invoice_type(self):
        """On top of the core rules, a customer marked for simplified invoices
        always gets a simplified document (F2/R5, or the F4 of a summary), and
        a regular customer refund defaults to R1 instead of R4."""
        previous = {move: move.l10n_es_invoice_type for move in self}
        res = super()._compute_l10n_es_invoice_type()
        for move in self:
            if (move.state == "posted" and previous[move]) or (
                move.country_code != "ES"
                or move.move_type not in ("out_invoice", "out_refund")
            ):
                continue
            if move.commercial_partner_id.aeat_simplified_invoice:
                if move.move_type == "out_refund":
                    move.l10n_es_invoice_type = "R5"
                elif move.l10n_es_invoice_type != "F4":
                    move.l10n_es_invoice_type = "F2"
            elif (
                move.move_type == "out_refund"
                and move.l10n_es_invoice_type == "R4"
                and previous[move] in (False, "R5")
            ):
                move.l10n_es_invoice_type = "R1"
        return res

    @api.depends(
        "move_type",
        "partner_id",
        "l10n_es_invoice_type",
        "journal_id.sii_simplified_invoices",
        "commercial_partner_id.aeat_simplified_invoice",
        "invoice_line_ids.tax_ids.l10n_es_type",
    )
    def _compute_sii_invoice_marks(self):
        """Simplified invoices go in their own series (art. 7.1.a RD
        1619/2012), so the journal tells them from the full ones: an invoice of
        a simplified series that identifies the customer is a qualified one; a
        full invoice without identification is only valid where art. 6.1.d does
        not require the customer's VAT number, an operation not located in
        Spain. Only the recipient of a vendor bill knows whether the supplier
        issued a qualified simplified invoice."""
        simplified_partner = self.env.ref(
            "l10n_es.partner_simplified", raise_if_not_found=False
        )
        for move in self:
            if move.state == "posted":
                continue
            invoice_type = move.l10n_es_invoice_type
            if not move.is_sale_document():
                move.sii_qualified_simplified_invoice = (
                    move.sii_qualified_simplified_invoice
                    and invoice_type in SII_QUALIFIED_SIMPLIFIED_TYPES
                )
                move.sii_unidentified_recipient_invoice = False
                continue
            simplified_series = move.journal_id.sii_simplified_invoices
            move.sii_qualified_simplified_invoice = (
                simplified_series and invoice_type in SII_QUALIFIED_SIMPLIFIED_TYPES
            )
            taxes = move.invoice_line_ids.tax_ids.flatten_taxes_hierarchy().filtered(
                lambda tax: tax.l10n_es_type != "ignore"
            )
            move.sii_unidentified_recipient_invoice = bool(
                not simplified_series
                and invoice_type in SII_UNIDENTIFIED_RECIPIENT_TYPES
                and taxes
                and all(tax.l10n_es_type == "no_sujeto_loc" for tax in taxes)
                and not move.commercial_partner_id.aeat_simplified_invoice
                and move.partner_id != simplified_partner
            )

    @api.depends(
        "fiscal_position_id.sii_regime_code_sale",
        "fiscal_position_id.sii_regime_code_purchase",
        "company_id.sii_enabled",
    )
    def _compute_l10n_es_regime_code(self):
        """For SII companies, the registration key forced by the fiscal position
        goes first, and a third key goes to the second additional one."""
        res = super()._compute_l10n_es_regime_code()
        for move in self:
            if move.state == "posted" and move.l10n_es_regime_code:
                continue
            if not move.company_id.sii_enabled or not move.is_invoice(
                include_receipts=True
            ):
                move.l10n_es_regime_code_additional2 = False
                continue
            codes = move._get_sii_regime_code_list() + [False, False]
            move.l10n_es_regime_code = codes[0]
            move.l10n_es_regime_code_additional = codes[1]
            move.l10n_es_regime_code_additional2 = codes[2]
        return res

    def _get_sii_regime_code_list(self):
        """Return the registration keys of the invoice, main one first.

        Like core, each product line gives the regime codes of its taxes, or the
        default code of the company when they have none, sorted by the core
        priority. A key forced by the fiscal position goes first and replaces
        the default code.
        """
        self.ensure_one()
        priorities = {"07": 0, "05": 1, "03": 2, "08": 2}
        default_code = self.company_id._get_sii_default_regime_code()
        codes = set()
        for line in self.invoice_line_ids.filtered(
            lambda line: line.display_type == "product"
        ):
            line_codes = {
                code
                for code in line.tax_ids.flatten_taxes_hierarchy().mapped(
                    "l10n_es_regime_code"
                )
                if code
            }
            codes |= line_codes or {default_code}
        use = "purchase" if self.is_purchase_document(include_receipts=True) else "sale"
        forced_code = self.fiscal_position_id._get_sii_forced_regime_code(use)
        if forced_code:
            codes -= {forced_code, default_code}
        sorted_codes = sorted(codes, key=lambda code: (priorities.get(code, 99), code))
        if forced_code:
            return [forced_code] + sorted_codes
        return sorted_codes or [default_code]

    def _get_sii_regime_codes(self):
        self.ensure_one()
        tax_model = self.env["account.tax"]
        codes = [
            tax_model._l10n_es_regime_code_aeat(code)
            for code in (
                self.l10n_es_regime_code,
                self.l10n_es_regime_code_additional,
                self.l10n_es_regime_code_additional2,
            )
            if code
        ]
        return codes or [self.company_id._get_sii_default_regime_code()]

    @api.depends(
        "move_type",
        "l10n_es_regime_code",
        "l10n_es_regime_code_additional",
        "l10n_es_regime_code_additional2",
    )
    def _compute_sii_property_required(self):
        """Leases of business premises (keys 12 and 13) need the data of the
        real property, also when the key is an additional one."""
        for invoice in self:
            invoice.sii_property_required = invoice.move_type in (
                "out_invoice",
                "out_refund",
            ) and bool(
                {"12_sale", "13_sale"}
                & {
                    invoice.l10n_es_regime_code,
                    invoice.l10n_es_regime_code_additional,
                    invoice.l10n_es_regime_code_additional2,
                }
            )

    @api.depends("amount_total")
    def _compute_macrodata(self):
        return super()._compute_macrodata()

    @api.depends("invoice_line_ids.tax_ids.l10n_es_type")
    def _compute_dua_invoice(self):
        for invoice in self:
            invoice.sii_dua_invoice = invoice.is_purchase_document() and (
                invoice._l10n_es_is_dua()
            )

    @api.depends("state", "aeat_state", "sii_needs_cancel")
    def _compute_sii_send_date_visible(self):
        for invoice in self:
            invoice.sii_send_date_visible = (
                invoice.state == "posted"
                and invoice.aeat_state not in ["sent", "cancelled"]
            ) or (
                invoice.state == "cancel"
                and invoice.sii_needs_cancel
                and invoice.aeat_state in ["sent", "sent_w_errors", "sent_modified"]
            )

    def _aeat_get_partner(self):
        return self.commercial_partner_id

    def _raise_exception_sii(self, field_name):
        raise UserError(
            self.env._(
                "You cannot change the %s of an invoice "
                "already registered at the SII. You must cancel the "
                "invoice and create a new one with the correct value",
                field_name,
            )
        )

    def write(self, vals):
        """For supplier invoices the SII primary key is the supplier
        VAT/ID Otro and the supplier invoice number. Cannot let change these
        values in a SII registered supplier invoice"""
        for invoice in self.filtered(
            lambda x: x.is_invoice() and x.aeat_state != "not_sent"
        ):
            if "invoice_date" in vals:
                self._raise_exception_sii(self.env._("invoice date"))
            elif "thirdparty_number" in vals:
                self._raise_exception_sii(self.env._("third-party number"))
            if invoice.move_type in ["in_invoice", "in_refund"]:
                if "partner_id" in vals:
                    correct_partners = invoice._aeat_get_partner()
                    correct_partners |= correct_partners.child_ids
                    if vals["partner_id"] not in correct_partners.ids:
                        self._raise_exception_sii(self.env._("supplier"))
                elif "ref" in vals:
                    self._raise_exception_sii(self.env._("supplier invoice number"))
            elif invoice.move_type in ["out_invoice", "out_refund"] and "name" in vals:
                self._raise_exception_sii(self.env._("invoice number"))
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
            raise UserError(
                self.env._("There's a mismatch in taxes for RE. Check them.")
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

    def _get_tax_info(self):
        # Use the method at l10n_es_aeat that returns the needed info
        return self._get_aeat_tax_info()

    def _get_sii_document_taxes(self):
        self.ensure_one()
        return (
            self.line_ids.tax_ids | self.line_ids.tax_line_id
        ).flatten_taxes_hierarchy()

    def _get_sii_tax_scope(self, tax):
        """Without a scope on the tax, the lines with the tax decide: services
        when all of them have a service product, goods otherwise."""
        if tax.tax_scope:
            return super()._get_sii_tax_scope(tax)
        lines = self.invoice_line_ids.filtered(
            lambda line: (
                line.display_type == "product"
                and tax in line.tax_ids.flatten_taxes_hierarchy()
            )
        )
        if lines and all(line.product_id.type == "service" for line in lines):
            return "service"
        return "consu"

    def _get_sii_base_not_in_total(self):
        self.ensure_one()
        sign = -1 if self.move_type[:3] == "out" else 1
        lines = self.invoice_line_ids.filtered(
            lambda line: (
                line.display_type == "product"
                and line.tax_ids
                and all(
                    tax.l10n_es_type == "ignore"
                    for tax in line.tax_ids.flatten_taxes_hierarchy()
                )
            )
        )
        return sum(lines.mapped("balance")) * sign

    def _get_sii_in_taxes(self):
        """Get the taxes for purchase invoices.

        :param self:  Single invoice record.
        """
        self.ensure_one()
        taxes_dict = {}
        tax_amount = 0.0
        not_in_amount_total = self._get_sii_base_not_in_total()
        tax_lines = self._get_aeat_tax_info()
        for tax_line in tax_lines.values():
            tax = tax_line["tax"]
            codes = self._get_sii_tax_codes(tax)
            not_in_amount_total += self._get_sii_amount_not_in_total(tax_line, codes)
            if "SFRISP" in codes:
                base_dict = taxes_dict.setdefault(
                    "InversionSujetoPasivo",
                    {"DetalleIVA": []},
                )
            elif codes & {"SFRS", "SFRNS", "SFRSA", "SFRND"}:
                base_dict = taxes_dict.setdefault("DesgloseIVA", {"DetalleIVA": []})
            else:
                continue
            tax_dict = self._get_sii_tax_dict(tax_line, tax_lines)
            if codes & {"SFRISP", "SFRS", "SFRSA"}:
                tax_amount += tax_line["deductible_amount"]
            if "SFRBI" in codes:
                tax_dict["BienInversion"] = "S"
            if "SFRNS" in codes:
                tax_dict.pop("TipoImpositivo")
                tax_dict.pop("CuotaSoportada")
                base_dict["DetalleIVA"].append(tax_dict)
            elif "SFRSA" in codes:
                tax_dict["PorcentCompensacionREAGYP"] = tax_dict.pop("TipoImpositivo")
                tax_dict["ImporteCompensacionREAGYP"] = tax_dict.pop("CuotaSoportada")
                base_dict["DetalleIVA"].append(tax_dict)
            else:
                if not self._merge_tax_dict(
                    base_dict["DetalleIVA"],
                    tax_dict,
                    ["TipoImpositivo", "BienInversion"],
                    ["BaseImponible", "CuotaSoportada"],
                ):
                    base_dict["DetalleIVA"].append(tax_dict)
        return taxes_dict, tax_amount, not_in_amount_total

    def _get_mapping_key(self):
        return self.move_type

    def _is_aeat_simplified_invoice(self):
        """Issued documents without an identified recipient: simplified
        invoices (F2), their refunds (R5) and summaries of them (F4). The AEAT
        rejects the counterpart on exactly these types; a simplified invoice
        that identifies the recipient (art. 7.2 and 7.3 RD 1619/2012) goes as F1
        or R1-R4. A received F2 or F4 always identifies its issuer."""
        self.ensure_one()
        return self.is_sale_document() and self.l10n_es_invoice_type in (
            "F2",
            "F4",
            "R5",
        )

    def _aeat_check_exceptions(self):
        res = super()._aeat_check_exceptions()
        if self.is_invoice() and not self.l10n_es_invoice_type:
            raise UserError(self.env._("The invoice type is required."))
        self._sii_check_invoice_type()
        if not self.ref and self.move_type in ["in_invoice", "in_refund"]:
            error_msg = self.env._("The supplier number invoice is required")
            raise UserError(error_msg)
        return res

    def _sii_check_invoice_type(self):
        """What the AEAT would reject because of the invoice type and its marks
        (errors 2022 and 2023, validations of simplified invoices)."""
        invoice_type = self.l10n_es_invoice_type
        if (
            self.sii_qualified_simplified_invoice
            and invoice_type not in SII_QUALIFIED_SIMPLIFIED_TYPES
        ):
            raise UserError(
                self.env._(
                    "A qualified simplified invoice (art. 7.2 and 7.3 RD "
                    "1619/2012) identifies the recipient: its type must be F1 or "
                    "R1-R4."
                )
            )
        if (
            self.sii_unidentified_recipient_invoice
            and invoice_type not in SII_UNIDENTIFIED_RECIPIENT_TYPES
        ):
            raise UserError(
                self.env._(
                    "An invoice without recipient identification (art. 6.1.d RD "
                    "1619/2012) must be of type F2 or R5."
                )
            )
        limited_types = ("F2", "R5") if self.is_purchase_document() else ("F2",)
        if (
            invoice_type in limited_types
            and not self.sii_unidentified_recipient_invoice
            and self.company_currency_id.compare_amounts(
                abs(self.amount_total_signed), SII_SIMPLIFIED_INVOICE_LIMIT
            )
            > 0
        ):
            raise UserError(
                self.env._(
                    "A simplified invoice cannot exceed %(limit)s euros (art. 4 "
                    "RD 1619/2012): it must be a full invoice, with the "
                    "recipient identified, or, for an operation not located in "
                    "Spain, an invoice without recipient identification (art. "
                    "6.1.d).",
                    limit=SII_SIMPLIFIED_INVOICE_LIMIT,
                )
            )
        if (
            self.move_type == "in_invoice"
            and invoice_type == "F2"
            and self._get_sii_in_taxes()[1]
        ):
            raise UserError(
                self.env._(
                    "A simplified invoice received (F2) does not give the right "
                    "to deduct VAT (art. 97 LIVA): use non deductible taxes or, if "
                    "it carries your company's VAT number, register it as a full "
                    "invoice (F1) marked as qualified simplified invoice."
                )
            )

    def _get_sii_invoice_type(self):
        self.ensure_one()
        return self.l10n_es_invoice_type

    def _get_aeat_invoice_dict_out(self, cancel=False):
        inv_dict = super()._get_aeat_invoice_dict_out(cancel=cancel)
        if cancel:
            return inv_dict
        if self.thirdparty_invoice:
            inv_dict["FacturaExpedida"]["EmitidaPorTercerosODestinatario"] = "S"
        if self.sii_property_required:
            inv_dict["FacturaExpedida"]["DatosInmueble"] = {
                "DetalleInmueble": {
                    "SituacionInmueble": self.sii_property_location,
                    "ReferenciaCatastral": (self.sii_property_cadastrial_code or ""),
                }
            }
        exp_dict = inv_dict["FacturaExpedida"]
        self._add_sii_operation_date(exp_dict)
        if self.sii_qualified_simplified_invoice:
            exp_dict["FacturaSimplificadaArticulos7.2_7.3"] = "S"
        if self.sii_unidentified_recipient_invoice:
            exp_dict["FacturaSinIdentifDestinatarioAritculo6.1.d"] = "S"
        if self.move_type == "out_refund":
            exp_dict["TipoRectificativa"] = self.sii_refund_type
        return inv_dict

    def _add_sii_operation_date(self, invoice_dict):
        """FechaOperacion of the invoices whose operation date, the delivery
        date of Odoo core, is not the invoice one, as the SII of Odoo core
        does (required by the key 14 of the public administrations works)."""
        if self.delivery_date and self.delivery_date != self.invoice_date:
            invoice_dict["FechaOperacion"] = self._change_date_format(
                self.delivery_date
            )

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
        periodo = self._get_document_period()
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
            invoice_type = self._get_sii_invoice_type()
            company_name = partner.name[0:120]
            if self.sii_dua_invoice:
                company_name = self.company_id.name

            regime_codes = self._get_sii_regime_codes()
            inv_dict["FacturaRecibida"] = {
                # TODO: Incluir los 5 tipos de facturas rectificativas
                "TipoFactura": invoice_type,
                "ClaveRegimenEspecialOTrascendencia": regime_codes[0],
                "DescripcionOperacion": self.sii_description,
                "DesgloseFactura": desglose_factura,
                "Contraparte": {"NombreRazon": company_name},
                "FechaRegContable": reg_date,
                "CuotaDeducible": tax_amount,
            }
            if not self.sii_dua_invoice:
                inv_dict["FacturaRecibida"]["ImporteTotal"] = (
                    -self.amount_total_signed - not_in_amount_total
                )
            if self.sii_macrodata:
                inv_dict["FacturaRecibida"].update(Macrodato="S")
            if self.sii_qualified_simplified_invoice:
                inv_dict["FacturaRecibida"]["FacturaSimplificadaArticulos7.2_7.3"] = "S"
            for index, regime_code in enumerate(regime_codes[1:], start=1):
                inv_dict["FacturaRecibida"][
                    f"ClaveRegimenEspecialOTrascendenciaAdicional{index}"
                ] = regime_code
            # Uso condicional de IDOtro/NIF
            inv_dict["FacturaRecibida"]["Contraparte"].update(ident)
            self._add_sii_operation_date(inv_dict["FacturaRecibida"])
            if self.move_type == "in_refund":
                inv_dict["FacturaRecibida"]["TipoRectificativa"] = self.sii_refund_type

            if self.sii_dua_invoice:
                inv_dict["FacturaRecibida"].pop("FechaOperacion", None)
                nif = self.company_id.partner_id._parse_aeat_vat_info()[2]
                inv_dict["FacturaRecibida"]["IDEmisorFactura"] = {"NIF": nif}
                inv_dict["IDFactura"]["IDEmisorFactura"] = {"NIF": nif}
                inv_dict["FacturaRecibida"]["Contraparte"]["NIF"] = nif
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

    @api.model
    def _get_valid_document_states(self):
        return SII_VALID_INVOICE_STATES

    def _cancel_invoice_to_sii(self, with_commit=False):
        self._cancel_document_to_sii(with_commit=with_commit)

    def cancel_sii(self):
        invoices = self.filtered(
            lambda i: (
                i.sii_enabled
                and i.state in ["cancel"]
                and i.aeat_state in ["sent", "sent_w_errors", "sent_modified"]
            )
        )
        if not invoices._cancel_send_to_sii():
            raise UserError(
                self.env._(
                    "You can not communicate the cancellation of this invoice "
                    "at this moment. Please, try again later."
                )
            )
        for invoice in invoices:
            company = invoice.company_id
            sii_sending_time = company._get_sii_sending_time()
            invoice.write({"sii_send_date": sii_sending_time, "sii_needs_cancel": True})
            # Create trigger if any company needs to send doc to SII now
            # so the sending to SII cron is executed as soon as possible
            if invoices.company_id.filtered(
                lambda company: (
                    company.send_mode == "auto"
                    or (company.send_mode == "delayed" and company.delay_time == 0.0)
                )
            ):
                self.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")._trigger()

    def button_cancel(self):
        if not self._cancel_send_to_sii():
            raise UserError(
                self.env._("You cannot cancel this invoice. Please, try again later.")
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
        if not self._cancel_send_to_sii():
            raise UserError(
                self.env._(
                    "You can not set to draft this invoice because"
                    " the SII trigger could not be cancelled."
                )
            )
        return super().button_draft()

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
                    names = [unidecode(x) for x in names if x]  # Avoid "ugly" chars
                    description += " - ".join(filter(None, names)).replace("\n", " ")
            invoice.sii_description = description or "/"  # shrink to 500 by the field

    @api.depends(
        "company_id",
        "company_id.sii_enabled",
        "company_id.sii_start_date",
        "journal_id",
        "journal_id.sii_enabled",
        "move_type",
        "fiscal_position_id",
        "fiscal_position_id.aeat_active",
        "date",
        "invoice_line_ids",
    )
    def _compute_sii_enabled(self):
        """Compute if the invoice is enabled for the SII"""
        for invoice in self:
            dua_taxes = invoice._get_dua_sii_exempt_taxes()
            if (
                invoice.company_id.sii_enabled
                and invoice.journal_id.sii_enabled
                and invoice.is_invoice()
            ):
                invoice.sii_enabled = (
                    (
                        (
                            invoice.fiscal_position_id
                            and invoice.fiscal_position_id.aeat_active
                        )
                        or not invoice.fiscal_position_id
                    )
                    and (
                        not dua_taxes
                        or not invoice.invoice_line_ids.filtered(
                            lambda x, dua_taxes=dua_taxes: bool(dua_taxes & x.tax_ids)
                        )
                    )
                    and (
                        not invoice.company_id.sii_start_date
                        or not invoice.date
                        or invoice.date >= invoice.company_id.sii_start_date
                    )
                )
            else:
                invoice.sii_enabled = False

    @api.model
    def _search_sii_enabled(self, operator, value):
        domain = super()._search_sii_enabled(operator, value)
        invoice_types = self.get_sale_types() + self.get_purchase_types()
        condition_1 = [("journal_id.sii_enabled", operator, value)]
        condition_2 = [("fiscal_position_id.aeat_active", operator, value)]
        search_ko = (operator == "in" and not value) or (operator == "not in" and value)
        exp_condition = Domain.OR if search_ko else Domain.AND
        condition_3 = []
        if not search_ko:
            condition_2 = Domain.OR([condition_2, [("fiscal_position_id", "=", False)]])
            for company in self.env.companies.filtered("sii_enabled"):
                if company.sii_start_date:
                    condition_3.append(
                        [
                            ("company_id", "=", company.id),
                            ("date", ">=", company.sii_start_date),
                        ]
                    )
                else:
                    condition_3.append([("company_id", "=", company.id)])
            if condition_3:
                condition_3 = Domain.OR(condition_3)
        conditions = [domain, condition_1, condition_2]
        if condition_3:
            conditions.append(condition_3)
        # Same exclusion as the compute: invoices with the DUA exempt tax
        dua_taxes = self.env["account.tax"]
        for company in self.env.companies.filtered("sii_enabled"):
            dua_taxes |= company._get_taxes_from_xmlids(
                ["account_tax_template_p_dua_exempt"]
            )
        if dua_taxes:
            conditions.append(
                [
                    (
                        "invoice_line_ids",
                        "any" if search_ko else "not any",
                        [("tax_ids", "in", dua_taxes.ids)],
                    )
                ]
            )
        return Domain.AND(
            [[("move_type", "in", invoice_types)], exp_condition(conditions)]
        )

    def _reverse_moves(self, default_values_list=None, cancel=False):
        # OVERRIDE
        if not default_values_list:
            default_values_list = [{} for move in self]
        for move, default_values in zip(self, default_values_list, strict=False):
            if move.move_type == "out_invoice" and move.country_code == "ES":
                # Core takes R4 for the refund of a regular invoice and R5 only
                # for F2/R5 originals: R1 (art. 80 One and Two LIVA) is the usual
                # cause, and the refund of a summary (F4) is simplified too
                default_values.setdefault(
                    "l10n_es_invoice_type",
                    "R5" if move._is_aeat_simplified_invoice() else "R1",
                )
            if move.sii_qualified_simplified_invoice:
                # A qualified simplified invoice is rectified by another one
                # (FAQ 2.50 of the SII: R1-R4 with the mark)
                default_values.setdefault("sii_qualified_simplified_invoice", True)
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

    def cancel_one_invoice(self, with_commit=False):
        self.sudo()._cancel_invoice_to_sii(with_commit=with_commit)

    @api.model
    def _write_sii_results(self, docs_vals):
        """Only SII fields are written, so skip the lines synchronization and the
        balance check done on each move write."""
        return super()._write_sii_results(
            {
                document.with_context(
                    check_move_validity=False, skip_invoice_sync=True
                ): doc_vals
                for document, doc_vals in docs_vals.items()
            }
        )

    @api.model
    def _send_to_sii_valid(self):
        remaining_documents = self.env["account.move"]
        documents = all_documents = self.search(
            [
                ("state", "in", self._get_valid_document_states()),
                (
                    "aeat_state",
                    "not in",
                    ["sent", "cancelled"],
                ),
                ("sii_send_date", "<=", fields.Datetime.now()),
            ]
        )
        if not documents:
            return remaining_documents
        batch = self._get_sii_batch()
        documents = all_documents[:batch]
        remaining_documents = all_documents - documents
        documents.confirm_one_document(with_commit=True)
        return remaining_documents

    @api.model
    def _send_to_sii_cancel(self):
        remaining_cancel_documents = self.env["account.move"]
        cancel_documents = all_cancel_documents = self.search(
            [
                ("state", "in", ["cancel"]),
                (
                    "aeat_state",
                    "in",
                    ["sent", "sent_w_errors", "sent_modified"],
                ),
                ("sii_needs_cancel", "=", True),
                ("sii_send_date", "<=", fields.Datetime.now()),
            ]
        )
        if cancel_documents:
            batch = self._get_sii_batch()
            cancel_documents = all_cancel_documents[:batch]
            remaining_cancel_documents = all_cancel_documents - cancel_documents
            cancel_documents.cancel_one_invoice(with_commit=True)
        return remaining_cancel_documents

    @api.model
    def _send_to_sii(self):
        remaining_documents = self._send_to_sii_valid()
        remaining_cancel_documents = self._send_to_sii_cancel()
        # Manage remaining invoices
        if remaining_documents or remaining_cancel_documents:
            self.env.ref("l10n_es_aeat_sii_oca.invoice_send_to_sii")._trigger()

    def _get_sii_tax_agency(self):
        if not self.journal_id.tax_agency_id:
            return super()._get_sii_tax_agency()
        return self.journal_id.tax_agency_id
