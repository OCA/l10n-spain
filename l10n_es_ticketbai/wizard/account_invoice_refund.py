# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models, api


class AccountInvoiceRefund(models.TransientModel):
    _inherit = 'account.invoice.refund'

    @api.multi
    def invoice_refund(self):
        data_refund = self.read(['filter_refund'])[0]['filter_refund']
        return super(AccountInvoiceRefund,
                     self.with_context(filter_refund=data_refund)).invoice_refund()

    @api.multi
    def compute_refund(self, mode='refund'):
        if 'modify' == mode:
            for invoice in self.env['account.invoice'].browse(
                    self._context.get('active_ids')):
                invoice.tbai_substitution_invoice_id = invoice.id
        return super().compute_refund(mode=mode)
