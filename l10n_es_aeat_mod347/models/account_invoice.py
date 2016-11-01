# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.one
    @api.depends('amount_untaxed_signed', 'tax_line_ids.amount')
    def _get_amount_total_wo_irpf(self):
        self.amount_total_wo_irpf = self.amount_untaxed_signed
        for tax_line_ids in self.tax_line_ids:
            if 'IRPF' not in tax_line_ids.name:
                self.amount_total_wo_irpf += tax_line_ids.amount

    amount_total_wo_irpf = fields.Float(
        compute="_get_amount_total_wo_irpf",
        string="Total amount without IRPF taxes")
    not_in_mod347 = fields.Boolean(
        "Not included in 347 report",
        help="If you mark this field, this invoice will not be included in "
             "any AEAT 347 model report.", default=False)
