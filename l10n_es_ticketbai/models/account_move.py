# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# Copyright 2021 Digital5, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, exceptions, fields, models

from odoo.addons.l10n_es_ticketbai_api.models.ticketbai_invoice import (
    RefundCode,
    RefundType,
    SiNoType,
)
from odoo.addons.l10n_es_ticketbai_api.ticketbai.xml_schema import TicketBaiSchema


class AccountMove(models.Model):
    _inherit = "account.move"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
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
        "Operation Description", default="/", copy=False
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
        comodel_name="tbai.vat.regime.key", string="VAT Regime Key", copy=True
    )
    tbai_vat_regime_key2 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 2nd Key", copy=True
    )
    tbai_vat_regime_key3 = fields.Many2one(
        comodel_name="tbai.vat.regime.key", string="VAT Regime 3rd Key", copy=True
    )

    @api.constrains("state")
    def _check_cancel_number_invoice(self):
        for record in self:
            if (
                record.tbai_enabled
                and "draft" == record.state
                and record.tbai_invoice_id
            ):
                raise exceptions.ValidationError(
                    _("You cannot change to draft a TicketBAI invoice!")
                )

    @api.model
    def create(self, vals):
        if vals and vals.get("company_id", False):
            company = self.env["res.company"].browse(vals["company_id"])
            if company.tbai_enabled:
                refund_method = self._context.get("refund_method", False)
                invoice_type = vals.get("move_type", False)
                if refund_method and invoice_type:
                    if "out_refund" == vals["move_type"]:
                        if "tbai_refund_type" not in vals:
                            vals["tbai_refund_type"] = RefundType.differences.value
                        if "tbai_refund_key" not in vals:
                            vals["tbai_refund_key"] = RefundCode.R1.value
                if vals.get("fiscal_position_id", False):
                    fiscal_position = self.env["account.fiscal.position"].browse(
                        vals["fiscal_position_id"]
                    )
                    vals["tbai_vat_regime_key"] = fiscal_position.tbai_vat_regime_key.id
                    vals[
                        "tbai_vat_regime_key2"
                    ] = fiscal_position.tbai_vat_regime_key2.id
                    vals[
                        "tbai_vat_regime_key3"
                    ] = fiscal_position.tbai_vat_regime_key3.id
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

    def tbai_prepare_invoice_values(self):
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
            "substitutes_simplified_invoice": (
                self.tbai_get_value_factura_emitida_sustitucion_simplificada()
            ),
            "tbai_customer_ids": [
                (
                    0,
                    0,
                    {
                        "name": partner.tbai_get_value_apellidos_nombre_razon_social(),
                        "country_code": partner.tbai_get_partner_country_code(),
                        "nif": partner.tbai_get_value_nif(),
                        "identification_number": (
                            partner.tbai_partner_identification_number or partner.vat
                        ),
                        "idtype": partner.tbai_partner_idtype,
                        "address": partner.tbai_get_value_direccion(),
                        "zip": partner.zip,
                    },
                )
            ],
            "description": self.tbai_description_operation[:250],
            "amount_total": "%.2f" % self.amount_total_signed,
            "vat_regime_key": self.tbai_vat_regime_key.code,
            "vat_regime_key2": self.tbai_vat_regime_key2.code,
            "vat_regime_key3": self.tbai_vat_regime_key3.code,
        }
        retencion_soportada = self.tbai_get_value_retencion_soportada()
        if retencion_soportada:
            vals["tax_retention_amount_total"] = retencion_soportada
        if self.tbai_is_invoice_refund():
            if RefundType.substitution.value == self.tbai_refund_type:
                refunded_invoice = self.tbai_substitution_invoice_id
                vals.update(
                    {
                        "substituted_invoice_amount_total_untaxed": (
                            refunded_invoice.tbai_get_value_base_rectificada()
                        ),
                        "substituted_invoice_total_tax_amount": (
                            refunded_invoice.tbai_get_value_cuota_rectificada()
                        ),
                    }
                )
            else:
                refunded_invoice = self.reversed_entry_id
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
                                    refunded_invoice.tbai_get_value_serie_factura()
                                ),
                                "number": (
                                    refunded_invoice.tbai_get_value_num_factura()
                                ),
                                "expedition_date": (
                                    refunded_invoice.tbai_get_value_fecha_exp_factura()
                                ),
                            },
                        )
                    ],
                }
            )
        operation_date = self.tbai_get_value_fecha_operacion()
        if operation_date:
            vals["operation_date"] = operation_date
        gipuzkoa_tax_agency = self.env.ref(
            "l10n_es_ticketbai_api.tbai_tax_agency_gipuzkoa"
        )
        tax_agency = self.company_id.tbai_tax_agency_id
        if tax_agency == gipuzkoa_tax_agency:
            lines = []
            for line in self.invoice_line_ids:
                lines.append(
                    (
                        0,
                        0,
                        {
                            "description": line.name[:250],
                            "quantity": line.tbai_get_value_cantidad(),
                            "price_unit": "%.8f" % line.price_unit,
                            "discount_amount": line.tbai_get_value_descuento(),
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
        for tax in self.invoice_line_ids.filtered(lambda x: x.tax_ids).mapped(
            "tax_ids"
        ):
            if tax not in exclude_taxes:
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
                exemption = self.fiscal_position_id.tbai_vat_exemption_ids.filtered(
                    lambda e: e.tax_id.id == tax["id"]
                )
                taxes.append(
                    (
                        0,
                        0,
                        {
                            "base": tax.tbai_get_value_base_imponible(self),
                            "is_subject_to": tax_subject_to,
                            "not_subject_to_cause": not_subject_to_cause,
                            "is_exempted": is_exempted,
                            "exempted_cause": is_exempted
                            and exemption.tbai_vat_exemption_key.code
                            or "",
                            "not_exempted_type": not_exempted_type,
                            "amount": "%.2f" % abs(tax.amount),
                            "amount_total": tax.tbai_get_value_cuota_impuesto(self),
                            "re_amount": tax.tbai_get_value_tipo_recargo_equiv(self)
                            or "",
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
            for record in self:
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
                lambda x: x.tbai_enabled and "posted" == x.state and x.tbai_invoice_id
            )
            tbai_invoices._tbai_invoice_cancel()
        return super().button_cancel()

    def _post(self, soft=True):
        if self.company_id.tbai_enabled:
            for inv in self:
                if inv.move_type == "out_refund" and not inv.reversed_entry_id:
                    raise exceptions.ValidationError(
                        _(
                            "You cannot validate a refund invoice "
                            "without the origin invoice!"
                        )
                    )
        res = super()._post(soft)
        # Remove move suffix if TBAI enabled and sale journal
        if self.company_id.tbai_enabled and "sale" == self.journal_id.type:
            no_suffix_name_len = len(self.sequence_prefix)
            for c in self.name[no_suffix_name_len:]:
                if not c.isdigit():
                    break
                no_suffix_name_len += 1
            self.name = self.name[:no_suffix_name_len]
        filter_refund = self._context.get("filter_refund", False)
        if not filter_refund or "refund" != filter_refund:
            # Do not send Credit Note to the Tax Agency when created
            # from Refund Wizard in 'refund' mode. Filter refund -> refund:
            # creates a draft credit note, not validated from wizard.
            tbai_invoices = self.sudo().filtered(
                lambda x: x.tbai_enabled
                and (
                    "out_invoice" == x.move_type
                    or (
                        x.reversed_entry_id
                        and "out_refund" == x.move_type
                        and x.tbai_refund_type
                        in [RefundType.differences.value, RefundType.substitution.value]
                        and x.reversed_entry_id.tbai_invoice_id
                        and not x.reversed_entry_id.tbai_cancellation_id
                    )
                )
            )
            tbai_invoices._tbai_build_invoice()
        return res

    def _get_refund_common_fields(self):
        refund_common_fields = super()._get_refund_common_fields()
        refund_common_fields.append("tbai_substitution_invoice_id")
        refund_common_fields.append("company_id")
        return refund_common_fields

    @api.model
    def _get_tax_grouping_key_from_tax_line(self, tax_line):
        vals = super()._get_tax_grouping_key_from_tax_line(tax_line)
        if self.fiscal_position_id:
            exemption = self.fiscal_position_id.tbai_vat_exemption_ids.filtered(
                lambda e: e.tax_id.id == tax_line.tax_line_id.id
            )
            if 1 == len(exemption):
                vals["tbai_vat_exemption_key"] = exemption.tbai_vat_exemption_key.id
        return vals

    @api.model
    def _get_tax_grouping_key_from_base_line(self, base_line, tax_vals):
        vals = super()._get_tax_grouping_key_from_base_line(base_line, tax_vals)
        if self.fiscal_position_id:
            exemption = self.fiscal_position_id.tbai_vat_exemption_ids.filtered(
                lambda e: e.tax_id.id == tax_vals["id"]
            )
            if 1 == len(exemption):
                vals["tbai_vat_exemption_key"] = exemption.tbai_vat_exemption_key.id
        return vals

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
        taxes = self.invoice_line_ids.filtered(
            lambda x: any([tax in irpf_taxes for tax in x.tax_ids])
        ).mapped("tax_ids")
        inv_id = self
        if 0 < len(taxes):
            res = "%.2f" % sum(
                [tax.tbai_get_amount_total_company(inv_id) for tax in taxes]
            )
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


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def tbai_get_value_cantidad(self):
        if RefundType.differences.value == self.move_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        return "%.2f" % (sign * self.quantity)

    def tbai_get_value_descuento(self):
        if self.discount:
            res = "%.2f" % (self.quantity * self.price_unit * self.discount / 100.0)
        else:
            res = "0.00"
        return res

    def tbai_get_value_importe_total(self):
        if RefundType.differences.value == self.move_id.tbai_refund_type:
            sign = -1
        else:
            sign = 1
        return "%.2f" % (sign * self.price_total)


class AccountMoveReversal(models.TransientModel):
    _inherit = "account.move.reversal"

    def _prepare_default_reversal(self, move):
        res = super()._prepare_default_reversal(move)
        res.update({"company_id": self.move_ids[0].company_id.id})
        return res
