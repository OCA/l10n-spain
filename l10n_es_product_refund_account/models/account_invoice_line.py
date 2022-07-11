# Copyright 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models


class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    def get_invoice_line_account(self, type, product, fpos, company):
        account_in = product.property_account_refund_in_id or \
            product.categ_id.property_account_refund_in_categ_id
        account_out = product.property_account_refund_out_id or \
            product.categ_id.property_account_refund_out_categ_id
        if type in ["in_refund"] and account_in:
            return account_in
        elif type in ["out_refund"] and account_out:
            return account_out
        else:
            return super().get_invoice_line_account(
                type, product, fpos, company)
