# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _prepare_asset_vals(self, aml):
        # Adapt purchase value for taking into account non deductible amounts
        # As we only know the deductible amount at invoice level, we get the general
        # tax info, and then apply the percentage corresponding to this line
        res = super()._prepare_asset_vals(aml)
        main_vals = aml.move_id._get_aeat_tax_info()
        amount = aml.balance
        for tax in aml.tax_ids:
            tax_vals = main_vals[tax]
            vals = {}
            aml._process_aeat_tax_base_info(vals, tax, 1)
            if tax_vals["amount"] != tax_vals["deductible_amount"]:
                ratio = vals[tax]["base"] / tax_vals["base"]
                diff = tax_vals["amount"] - tax_vals["deductible_amount"]
                amount += diff * ratio
        res["purchase_value"] = amount
        return res
