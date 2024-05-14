# Copyright 2023 Moduon - Eduardo de Miguel
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_es_aeat_real_estate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.real_estate",
        string="Real Estate",
        help="Real Estate related to this move line",
        domain="[('company_id', '=', company_id), ('partner_id', '=', partner_id)]",
    )

    def _process_aeat_tax_base_info(self, res, tax, sign):
        """It modifies the dictionary given in res for setting the base amount info
        for the taxes dictionary obtained in ~~account.move~~._get_aeat_tax_info().
        """
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        for tax in taxes:
            res.setdefault(
                tax, {"tax": tax, "base": 0, "amount": 0, "deductible_amount": 0}
            )
            res[tax]["base"] += self.balance * sign

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        """It modifies the dictionary given in res for setting the tax amount info
        for the taxes dictionary obtained in ~~account.move~~._get_aeat_tax_info().
        """
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        for tax in taxes:
            res.setdefault(
                tax, {"tax": tax, "base": 0, "amount": 0, "deductible_amount": 0}
            )
            amount = self.balance * sign
            res[tax]["amount"] += amount
            res[tax]["deductible_amount"] += amount
