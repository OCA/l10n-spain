# Copyright 2020 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, api, exceptions, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    def post(self):
        super().post()
        for move in self:
            for aml in move.line_ids.filtered("asset_id"):
                aml.asset_id.write(aml._get_asset_analytic_values())


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_prorrate_percent = fields.Float(string="Prorrate perc.", default=100)

    def _get_asset_analytic_values(self):
        """Get assets values according prorrata"""
        self.ensure_one()
        vat_prorrate_percent = self.vat_prorrate_percent
        if vat_prorrate_percent == 100 or not self.asset_profile_id:
            return {}
        totals = self.tax_ids.compute_all(self.asset_id.purchase_value)
        total_tax = totals["total_included"] - totals["total_excluded"]
        increment = total_tax * (100 - vat_prorrate_percent) / 100
        return {
            "purchase_value": self.asset_id.purchase_value + increment,
            "vat_prorrate_percent": vat_prorrate_percent,
            "vat_prorrate_increment": increment,
        }

    @api.constrains("vat_prorrate_percent")
    def check_vat_prorrate_percent(self):
        for line in self:
            if not (0 < line.vat_prorrate_percent <= 100):
                raise exceptions.ValidationError(
                    _("VAT prorrate percent must be between 0.01 and 100")
                )
