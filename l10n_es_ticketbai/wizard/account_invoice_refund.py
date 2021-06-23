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
