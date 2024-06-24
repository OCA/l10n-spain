# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models

from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import (
    RefundCode,
    RefundType,
    SiNoType,
    TicketBaiInvoiceState,
)
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema


class AccountMove(models.Model):
    _inherit = "account.move"

    def _default_tbai_vat_regime_key(self):
        context = self.env.context
        invoice_type = context.get("move_type", context.get("default_move_type"))
        if invoice_type in ["out_invoice", "out_refund"]:
            key = self.env["tbai.vat.regime.key"].search([("code", "=", "01")], limit=1)
            return key

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
    tbai_send_invoice = fields.Boolean(related="journal_id.tbai_send_invoice")
    tbai_substitution_invoice_id = fields.Many2one(
        comodel_name="account.move",
        copy=False,
        help="Link between a validated Customer Invoice and its substitute.",
    )
    tbai_invoice_id = fields.Many2one(
        comodel_name="tbai.invoice", string="TicketBAI Invoice", copy=False
    )
    tbai_invoice_ids = fields.One2many(
        comodel_name="tbai.invoice",
        inverse_name="invoice_id",
        string="TicketBAI Invoices",
    )
    tbai_cancellation_id = fields.Many2one(
        comodel_name="tbai.invoice", string="TicketBAI Cancellation", copy=False
    )
    tbai_cancellation_ids = fields.One2many(
        comodel_name="tbai.invoice",
        inverse_name="cancelled_invoice_id",
        string="TicketBAI Cancellations",
    )
    tbai_response_ids = fields.Many2many(
        comodel_name="tbai.response",
        compute="_compute_tbai_response_ids",
        string="Responses",
    )
    tbai_datetime_invoice = fields.Datetime(
        compute="_compute_tbai_datetime_invoice", store=True, copy=False
    )
    tbai_date_operation = fields.Datetime("Operation Date", copy=False)
    tbai_description_operation = fields.Text(
        "Operation Description",
        default="/",
        copy=False,
        compute="_compute_tbai_description",
        store=True,
    )
    tbai_substitute_simplified_invoice = fields.Boolean(
        "Substitute Simplified Invoice", copy=False
    )
    tbai_refund_key = fields.Selection(
        selection=[
            (RefundCode.R1.value, "Art. 80.1, 80.2, 80.6 and rights founded error"),
            (RefundCode.R2.value, "Art. 80.3"),
            (RefundCode.R3.value, "Art. 80.4"),
            (RefundCode.R4.value, "Art. 80 - other"),
            (RefundCode.R5.value, "Simplified Invoice"),
        ],
        help="BOE-A-1992-28740. Ley 37/1992, de 28 de diciembre, del Impuesto sobre el "
        "Valor Añadido. Artículo 80. Modificación de la base imponible.",
        copy=False,
    )
    tbai_refund_type = fields.Selection(
        selection=[
            # (RefundType.substitution.value, 'By substitution'), TODO: Remove from code
            (RefundType.differences.value, "By differences")
        ],
        copy=False,
    )
    tbai_vat_regime_key = fields.Many2one(
        comodel_name="tbai.vat.regime.key",
        string="VAT Regime Key",
        copy=True,
        default=_default_tbai_vat_regime_key,
    )
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 2nd Key", copy=True
    )
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 3rd Key", copy=True
    )
    tbai_refund_origin_ids = fields.One2many(
        comodel_name="tbai.invoice.refund.origin",
        inverse_name="account_refund_invoice_id",
        string="TicketBAI Refund Origin References",
    )

    @api.constrains("state")
    def _check_cancel_number_invoice(self):
        for record in self:
            if (
                record.move_type in ("out_invoice", "out_refund")
                and record.tbai_enabled
                and "draft" == record.state
                and record.tbai_invoice_id
            ):
                raise exceptions.ValidationError(
                    _("You cannot change to draft a TicketBAI invoice!")
                )

    @api.model
    def create(self, vals):
        if vals.get("company_id", False):
            company = self.env["res.company"].browse(vals["company_id"])
        else:
            company = self.env.company
        if company.tbai_enabled:
            invoice_type = vals.get("move_type", False) or self._context.get(
                "default_move_type", False
            )
            refund_method = (
                self._context.get("refund_method", False)
                or invoice_type == "out_refund"
            )
            if refund_method and invoice_type:
                if "out_refund" == invoice_type:
                    if not vals.get("tbai_refund_type", False):
                        vals["tbai_refund_type"] = RefundType.differences.value
                    if not vals.get("tbai_refund_key", False):
                        if vals.get("partner_id", False):
                            partner = self.env["res.partner"].browse(vals["partner_id"])
                            if partner.aeat_anonymous_cash_customer:
                                vals["tbai_refund_key"] = RefundCode.R5.value
                            else:
                                vals["tbai_refund_key"] = RefundCode.R1.value
                        else:
                            vals["tbai_refund_key"] = RefundCode.R1.value
            if vals.get("fiscal_position_id", False):
                fiscal_position = self.env["account.fiscal.position"].browse(
                    vals["fiscal_position_id"]
                )
                vals["tbai_vat_regime_key"] = fiscal_position.tbai_vat_regime_key.id
                vals["tbai_vat_regime_key2"] = fiscal_position.tbai_vat_regime_key2.id
                vals["tbai_vat_regime_key3"] = fiscal_position.tbai_vat_regime_key3.id
            if "name" in vals and vals["name"]:
                vals["tbai_description_operation"] = vals["name"]
        return super().create(vals)

    @api.depends(
        "tbai_invoice_ids",
        "tbai_invoice_ids.state",
        "tbai_cancellation_ids",
        "tbai_cancellation_ids.state",
    )
    def _compute_tbai_response_ids(self):
        for record in self:
            response_ids = record.tbai_invoice_ids.mapped("tbai_response_ids").ids
            response_ids += record.tbai_cancellation_ids.mapped("tbai_response_ids").ids
            record.tbai_response_ids = [(6, 0, response_ids)]

    @api.depends("date", "invoice_date")
    def _compute_tbai_datetime_invoice(self):
        for record in self:
            record.tbai_datetime_invoice = fields.Datetime.now()

    @api.onchange("fiscal_position_id", "partner_id")
    def onchange_fiscal_position_id_tbai_vat_regime_key(self):
        if self.fiscal_position_id:
            self.tbai_vat_regime_key = self.fiscal_position_id.tbai_vat_regime_key.id
            self.tbai_vat_regime_key2 = self.fiscal_position_id.tbai_vat_regime_key2.id
            self.tbai_vat_regime_key3 = self.fiscal_position_id.tbai_vat_regime_key3.id

    @api.onchange("reversed_entry_id")
    def onchange_tbai_reversed_entry_id(self):
        if self.reversed_entry_id:
            if not self.tbai_refund_type:
                self.tbai_refund_type = RefundType.differences.value
            if not self.tbai_refund_key:
                if not self.partner_id.aeat_anonymous_cash_customer:
                    self.tbai_refund_key = RefundCode.R1.value
                else:
                    self.tbai_refund_key = RefundCode.R5.value

    def tbai_prepare_invoice_values(self):
        def tbai_prepare_refund_values():
            refunded_inv = self.reversed_entry_id
            if refunded_inv:
                vals.update(
                    {
                        "is_invoice_refund": True,
                        "refund_code": self.tbai_refund_key,
                        "refund_type": self.tbai_refund_type,
                        "tbai_invoice_refund_ids": [
                            (
                                0,
                                0,
                                {
                                    "number_prefix": (
                                        refunded_inv.tbai_get_value_serie_factura()
                                    ),
                                    "number": (
                                        refunded_inv.tbai_get_value_num_factura()
                                    ),
                                    "expedition_date": (
                                        refunded_inv.tbai_get_value_fecha_exp_factura()
                                    ),
                                },
                            )
                        ],
                    }
                )
            else:
                if self.tbai_refund_origin_ids:
                    refund_id_dicts = []
                    for refund_origin_id in self.tbai_refund_origin_ids:
                        expedition_date = fields.Date.from_string(
                            refund_origin_id.expedition_date
                        ).strftime("%d-%m-%Y")
                        refund_id_dicts.append(
                            (
                                0,
                                0,
                                {
                                    "number_prefix": refund_origin_id.number_prefix,
                                    "number": refund_origin_id.number,
                                    "expedition_date": expedition_date,
                                },
                            )
                        )
                    vals.update(
                        {
                            "is_invoice_refund": True,
                            "refund_code": self.tbai_refund_key,
                            "refund_type": self.tbai_refund_type,
                            "tbai_invoice_refund_ids": refund_id_dicts,
                        }
                    )

        self.ensure_one()
        partner = self.partner_id
        vals = {
            "invoice_id": self.id,
            "schema": TicketBaiSchema.TicketBai.value,
            "name": self._get_move_display_name(),
            "company_id": self.company_id.id,
            "number_prefix": self.tbai_get_value_serie_factura(),
            "number": self.tbai_get_value_num_factura(),
            "expedition_date": self.tbai_get_value_fecha_exp_factura(),
            "expedition_hour": self.tbai_get_value_hora_exp_factura(),
            "simplified_invoice": self.tbai_get_value_simplified_invoice(),
            "substitutes_simplified_invoice": (
                self.tbai_get_value_factura_emitida_sustitucion_simplificada()
            ),
            "description": self.tbai_description_operation[:250],
            "amount_total": "%.2f" % self.amount_total_signed,
            "vat_regime_key": self.tbai_vat_regime_key.code,
            "vat_regime_key2": self.tbai_vat_regime_key2.code,
            "vat_regime_key3": self.tbai_vat_regime_key3.code,
        }
        if partner and not partner.aeat_anonymous_cash_customer:
            vals["tbai_customer_ids"] = [
                (
                    0,
                    0,
                    {
                        "name": partner.tbai_get_value_apellidos_nombre_razon_social(),
                        "country_code": partner._parse_aeat_vat_info()[0],
                        "nif": partner.tbai_get_value_nif(),
                        "identification_number": (
                            partner.tbai_partner_identification_number or partner.vat
                        ),
                        "idtype": partner.tbai_partner_idtype,
                        "address": partner.tbai_get_value_direccion(),
                        "zip": partner.zip,
                    },
                )
            ]
        retencion_soportada = self.tbai_get_value_retencion_soportada()
        if retencion_soportada:
            vals["tax_retention_amount_total"] = retencion_soportada
        if (
            self.tbai_is_invoice_refund()
            and RefundType.differences.value == self.tbai_refund_type
        ):
            tbai_prepare_refund_values()
        operation_date = self.tbai_get_value_fecha_operacion()
        if operation_date:
            vals["operation_date"] = operation_date
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa"
        )
        araba_tax_agency = self.env.ref("l10n_es_ticketbai_api.tbai_tax_agency_araba")
        tax_agency = self.company_id.tbai_tax_agency_id
        if tax_agency in (gipuzkoa_tax_agency, araba_tax_agency):
            lines = []
            for line in self.invoice_line_ids.filtered(
                lambda l: l.display_type not in ["line_note", "line_section"]
            ):
                description_line = line.name[:250] if line.name else ""
                if (
                    self.company_id.tbai_protected_data
                    and self.company_id.tbai_protected_data_txt
                ):
                    description_line = self.company_id.tbai_protected_data_txt[:250]
                price_unit = line.tbai_get_price_unit()
                lines.append(
                    (
                        0,
                        0,
                        {
                            "description": description_line,
                            "quantity": line.tbai_get_value_cantidad(),
                            "price_unit": "%.8f" % price_unit,
                            "discount_amount": line.tbai_get_value_descuento(
                                price_unit
                            ),
                            "amount_total": line.tbai_get_value_importe_total(),
                        },
                    )
                )
            vals["tbai_invoice_line_ids"] = lines
        taxes = []
        # Discard RecargoEquivalencia and IRPF Taxes
        tbai_maps = self.env["tbai.tax.map"].search([("code", "in", ("RE", "IRPF"))])
        exclude_taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        for tax in (
            self.invoice_line_ids.filtered(lambda x: x.tax_ids)
            .mapped("tax_ids")
            .filtered(lambda t: t not in exclude_taxes)
        ):
            tax_subject_to = tax.tbai_is_subject_to_tax()
            not_subject_to_cause = (
                not tax_subject_to and tax.tbai_get_value_causa(self) or ""
            )
            is_exempted = tax_subject_to and tax.tbai_is_tax_exempted() or False
            not_exempted_type = (
                tax_subject_to
                and not is_exempted
                and tax.tbai_get_value_tipo_no_exenta()
                or ""
            )
            exemption = ""
            if tax.tbai_is_tax_exempted():
                if self.fiscal_position_id:
                    exemption = self.fiscal_position_id.tbai_vat_exemption_ids.filtered(
                        lambda e: e.tax_id.id == tax["id"]
                    )
                    if len(exemption) == 1:
                        exemption = exemption.tbai_vat_exemption_key.code
                else:
                    exemption = self.env["tbai.vat.exemption.key"].search(
                        [("code", "=", "E1")], limit=1
                    )
                    exemption = exemption.code
            taxes.append(
                (
                    0,
                    0,
                    {
                        "base": tax.tbai_get_value_base_imponible(self),
                        "is_subject_to": tax_subject_to,
                        "not_subject_to_cause": not_subject_to_cause,
                        "is_exempted": is_exempted,
                        "exempted_cause": is_exempted and exemption or "",
                        "not_exempted_type": not_exempted_type,
                        "amount": "%.2f" % abs(tax.amount),
                        "amount_total": tax.tbai_get_value_cuota_impuesto(self),
                        "re_amount": tax.tbai_get_value_tipo_recargo_equiv(self) or "",
                        "re_amount_total": (
                            tax.tbai_get_value_cuota_recargo_equiv(self) or ""
                        ),
                        "surcharge_or_simplified_regime": (
                            tax.tbai_get_value_op_recargo_equiv_o_reg_simpl(self)
                        ),
                        "type": tax.tbai_get_value_tax_type(),
                    },
                )
            )
        vals["tbai_tax_ids"] = taxes
        return vals

    def _tbai_build_invoice(self):
        for record in self:
            vals = record.tbai_prepare_invoice_values()
            tbai_invoice = record.env["tbai.invoice"].create(vals)
            tbai_invoice.build_tbai_invoice()
            record.tbai_invoice_id = tbai_invoice.id

    def tbai_prepare_cancellation_values(self):
        self.ensure_one()
        vals = {
            "cancelled_invoice_id": self.id,
            "schema": TicketBaiSchema.AnulaTicketBai.value,
            "name": "{} - {}".format(_("Cancellation"), self.name),
            "company_id": self.company_id.id,
            "number_prefix": self.tbai_get_value_serie_factura(),
            "number": self.tbai_get_value_num_factura(),
            "expedition_date": self.tbai_get_value_fecha_exp_factura(),
        }
        return vals

    def _tbai_invoice_cancel(self):
        for record in self:
            vals = record.tbai_prepare_cancellation_values()
            tbai_invoice = record.env["tbai.invoice"].create(vals)
            tbai_invoice.build_tbai_invoice()
            record.tbai_cancellation_id = tbai_invoice.id

    def button_cancel(self):
        if self.company_id.tbai_enabled:
            for record in self.filtered(
                lambda m: m.move_type in self.get_invoice_types()
            ):
                non_cancelled_refunds = record.reversal_move_id.filtered(
                    lambda x: "cancel" != x.state
                )

                if len(non_cancelled_refunds) > 0:
                    raise exceptions.ValidationError(
                        _(
                            "Refund invoices must be cancelled in order "
                            "to cancel the original invoice."
                        )
                    )

                tbai_invoices = record.sudo().filtered(
                    lambda x: x.tbai_enabled
                    and "posted" == x.state
                    and x.tbai_invoice_id
                )
                tbai_invoices._tbai_invoice_cancel()
        return super().button_cancel()

    def _post(self, soft=True):
        def validate_refund_invoices():
            for invoice in refund_invoices:
                valid_refund = True
                error_refund_msg = None
                if not invoice.reversed_entry_id and not invoice.tbai_refund_origin_ids:
                    valid_refund = False
                    error_refund_msg = _(
                        "Please, specify data for the original"
                        " invoices that are going to be refunded"
                    )
                if invoice.reversed_entry_id.tbai_invoice_id:
                    valid_refund = invoice.reversed_entry_id.tbai_invoice_id.state in [
                        TicketBaiInvoiceState.pending.value,
                        TicketBaiInvoiceState.sent.value,
                    ]
                    if not valid_refund:
                        error_refund_msg = _(
                            "Some of the original invoices have related tbai invoices "
                            "in inconsistent state please fix them beforehand."
                        )
                if valid_refund and invoice.reversed_entry_id.tbai_cancellation_id:
                    valid_refund = False
                    error_refund_msg = _(
                        "Some of the original invoices "
                        "have related tbai cancelled invoices"
                    )
                if not valid_refund:
                    raise exceptions.ValidationError(error_refund_msg)

        res = super()._post(soft)
        tbai_invoices = self.sudo().env["account.move"]
        tbai_invoices |= self.sudo().filtered(
            lambda x: x.tbai_enabled
            and "out_invoice" == x.move_type
            and x.tbai_send_invoice
        )
        refund_invoices = self.sudo().filtered(
            lambda x: x.tbai_enabled
            and "out_refund" == x.move_type
            and (
                not x.tbai_refund_type
                or x.tbai_refund_type == RefundType.differences.value
            )
            and x.tbai_send_invoice
        )

        validate_refund_invoices()
        tbai_invoices |= refund_invoices
        tbai_invoices._tbai_build_invoice()
        return res

    def _get_refund_common_fields(self):
        refund_common_fields = super()._get_refund_common_fields()
        refund_common_fields.append("tbai_substitution_invoice_id")
        refund_common_fields.append("company_id")
        return refund_common_fields

    def tbai_is_invoice_refund(self):
        if "out_refund" == self.move_type or (
            "out_invoice" == self.move_type
            and RefundType.substitution.value == self.tbai_refund_type
        ):
            res = True
        else:
            res = False
        return res

    def tbai_get_value_serie_factura(self):
        num_invoice = ""
        for char in self.name[::-1]:
            if not char.isdigit():
                break
            num_invoice = char + num_invoice

        a = self.name[: (len(self.name) - len(num_invoice))]
        return a

    def tbai_get_value_num_factura(self):
        num_invoice = ""
        for char in self.name[::-1]:
            if not char.isdigit():
                break
            num_invoice = char + num_invoice
        return num_invoice

    def tbai_get_value_fecha_exp_factura(self):
        invoice_date = self.date or self.invoice_date
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(invoice_date)
        )
        return date.strftime("%d-%m-%Y")

    def tbai_get_value_hora_exp_factura(self):
        invoice_datetime = self.tbai_datetime_invoice
        date = fields.Datetime.context_timestamp(
            self, fields.Datetime.from_string(invoice_datetime)
        )
        return date.strftime("%H:%M:%S")

    def tbai_get_value_simplified_invoice(self):
        if self.partner_id.aeat_anonymous_cash_customer:
            res = SiNoType.S.value
        else:
            res = SiNoType.N.value
        return res

    def tbai_get_value_factura_emitida_sustitucion_simplificada(self):
        if self.tbai_substitute_simplified_invoice:
            res = SiNoType.S.value
        else:
            res = SiNoType.N.value
        return res

    def tbai_get_value_base_rectificada(self):
        return "%.2f" % abs(self.amount_untaxed_signed)

    def tbai_get_value_cuota_rectificada(self):
        amount = abs(self.amount_total_signed - self.amount_untaxed_signed)
        return "%.2f" % amount

    def tbai_get_value_fecha_operacion(self):
        if self.tbai_date_operation:
            tbai_date_operation = self.tbai_date_operation.strftime("%d-%m-%Y")
            date_invoice = (self.date or self.invoice_date).strftime("%d-%m-%Y")
            if tbai_date_operation == date_invoice:
                tbai_date_operation = None
        else:
            tbai_date_operation = None
        return tbai_date_operation

    def tbai_get_value_retencion_soportada(self):
        tbai_maps = self.env["tbai.tax.map"].search([("code", "=", "IRPF")])
        irpf_taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        taxes = self.mapped("invoice_line_ids.tax_ids") & irpf_taxes
        inv_id = self
        if 0 < len(taxes):
            if RefundType.differences.value == self.tbai_refund_type:
                sign = 1
            else:
                sign = -1
            amount_total = sum(
                tax.tbai_get_amount_total_company(inv_id) for tax in taxes
            )
            res = "%.2f" % (sign * amount_total)
        else:
            res = None
        return res

    def copy_data(self, default=None):
        res = super().copy_data(default=default)

        res[0].update(
            {"tbai_substitution_invoice_id": self.tbai_substitution_invoice_id.id}
        )
        res[0].update({"company_id": self.company_id.id})

        return res

    @api.depends(
        "invoice_line_ids",
        "invoice_line_ids.name",
        "company_id",
    )
    def _compute_tbai_description(self):
        default_description = self.default_get(["tbai_description_operation"])[
            "tbai_description_operation"
        ]
        for invoice in self.filtered(lambda inv: not inv.tbai_invoice_id):
            description = ""
            method = invoice.company_id.tbai_description_method
            if method == "fixed":
                description = invoice.company_id.tbai_description or default_description
            elif method == "manual":
                if invoice.tbai_description_operation != default_description:
                    # keep current content if not default
                    description = invoice.tbai_description_operation
            else:  # auto method
                if invoice.invoice_line_ids:
                    names = invoice.mapped("invoice_line_ids.name") or invoice.mapped(
                        "invoice_line_ids.ref"
                    )
                    description += " - ".join(filter(None, names))
            invoice.tbai_description_operation = (description or "")[:250] or "/"


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def tbai_get_value_cantidad(self):
        if RefundType.differences.value == self.move_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        return "%.2f" % (sign * self.quantity)

    def tbai_get_value_descuento(self, price_unit):
        if self.discount:
            if RefundType.differences.value == self.move_id.tbai_refund_type:
                sign = -1
            else:
                sign = 1
            res = "%.2f" % (sign * self.quantity * price_unit * self.discount / 100.0)
        else:
            res = "0.00"
        return res

    def tbai_get_value_importe_total(self):
        tbai_maps = self.env["tbai.tax.map"].search([("code", "=", "IRPF")])
        irpf_taxes = self.company_id.get_taxes_from_templates(
            tbai_maps.mapped("tax_template_ids")
        )
        currency = self.move_id and self.move_id.currency_id or None
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        taxes = (self.tax_ids - irpf_taxes).compute_all(
            price,
            currency,
            self.quantity,
            product=self.product_id,
            partner=self.move_id.partner_id,
        )
        price_total = taxes["total_included"] if taxes else self.price_subtotal
        invoice_id = self.move_id
        if invoice_id.currency_id.id != invoice_id.company_id.currency_id.id:
            price_total = currency._convert(
                price_total,
                invoice_id.company_id.currency_id,
                invoice_id.company_id,
                invoice_id.date or invoice_id.invoice_date,
            )
        if RefundType.differences.value == self.move_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        return "%.2f" % (sign * price_total)

    def tbai_get_price_unit(self):
        price_unit = self.price_unit
        for tax in self.tax_ids.filtered(lambda t: t.price_include):
            price_unit = price_unit - (
                self.price_unit * tax.amount / (100 + tax.amount)
            )
        currency = self.move_id and self.move_id.currency_id or None
        invoice_id = self.move_id
        if invoice_id.currency_id.id != invoice_id.company_id.currency_id.id:
            price_unit = currency._convert(
                price_unit,
                invoice_id.company_id.currency_id,
                invoice_id.company_id,
                invoice_id.date or invoice_id.invoice_date,
            )
        return price_unit
