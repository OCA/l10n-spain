# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_tax_quote_info(self, res, tax, line, sign):
        # In case the line comes from a vat_prorate, we don't need to add it
        super()._get_tax_quote_info(res, tax, line, sign)
        if line.vat_prorate:
            res[tax]["quote_amount"] -= line.balance * sign
