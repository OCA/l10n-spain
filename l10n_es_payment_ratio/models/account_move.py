# Copyright 2024 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class AccountMove(models.Model):

    _inherit = "account.move"

    payment_date = fields.Date(compute="_compute_amount", store=True)
    payment_ratio_create = fields.Float(compute="_compute_amount", store=True)
    payment_ratio_bill_date = fields.Float(compute="_compute_amount", store=True)
    payment_ratio_validation = fields.Float(compute="_compute_amount", store=True)

    @api.depends()
    def _compute_amount(self):
        super(AccountMove, self)._compute_amount()
        for record in self:
            if (
                record.state == "posted"
                and record.is_purchase_document()
                and tools.float_is_zero(
                    record.amount_residual,
                    precision_rounding=record.currency_id.rounding,
                )
            ):
                payments = (
                    record.line_ids.matched_debit_ids.debit_move_id
                    | record.line_ids.matched_credit_ids.credit_move_id
                )
                date = (
                    payments and max(payments.move_id.mapped("date"))
                ) or record.date
                record.payment_date = date
                record.payment_ratio_create = (
                    -record.amount_total_signed
                    * (date - record.create_date.date()).days
                )
                record.payment_ratio_bill_date = (
                    -record.amount_total_signed
                    * (date - (record.invoice_date or record.date)).days
                )
                record.payment_ratio_validation = (
                    -record.amount_total_signed * (date - record.date).days
                )
            else:
                record.payment_date = False
                record.payment_ratio_create = 0.0
                record.payment_ratio_bill_date = 0.0
                record.payment_ratio_validation = 0.0
