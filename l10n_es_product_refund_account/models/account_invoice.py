# Copyright 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.model
    def _prepare_refund(self, invoice, date_invoice=None, date=None,
                        description=None, journal_id=None):
        Product = self.env["product.product"]
        values = super()._prepare_refund(
            invoice, date_invoice, date, description, journal_id)
        if not values["type"] in ["out_refund", "in_refund"]:
            return values
        new_lines = []
        for data in values["invoice_line_ids"]:
            line = data[2]
            if not line["product_id"]:
                new_lines.append((0, 0, line))
                continue
            product = Product.browse(line["product_id"])
            account_in = product.property_account_refund_in_id or \
                product.categ_id.property_account_refund_in_categ_id
            account_out = product.property_account_refund_out_id or \
                product.categ_id.property_account_refund_out_categ_id
            if values["type"] in ["in_refund"] and account_in:
                line["account_id"] = account_in.id
            elif values["type"] in ["out_refund"] and account_out:
                line["account_id"] = account_out.id
            new_lines.append((0, 0, line))
        if new_lines:
            values["invoice_line_ids"] = new_lines
        return values
