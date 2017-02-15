# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_total_wo_irpf = fields.Float(
        compute="_compute_amount_total_wo_irpf", store=True,
        string="Total amount without IRPF taxes",
    )
    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
             "any AEAT 347 model report.", default=False,
    )

    @api.multi
    @api.depends('amount_untaxed_signed', 'tax_line_ids.amount')
    def _compute_amount_total_wo_irpf(self):
        for invoice in self:
            invoice.amount_total_wo_irpf = (
                # TODO: Make match by tax itself, not tax name
                invoice.amount_untaxed + sum(
                    invoice.tax_line_ids.filtered(
                        lambda t: 'IRPF' not in t.name
                    ).mapped('amount')
                )
            )
