# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        # Nullify tax fee for OSS taxes
        result = super()._process_aeat_tax_fee_info(res, tax, sign)
        oss_taxes = self.env["account.tax"].search(
            [("oss_country_id", "!=", False), ("company_id", "=", self.company_id.id)]
        )
        if tax in oss_taxes:
            res[tax]["amount"] = 0
        return result
