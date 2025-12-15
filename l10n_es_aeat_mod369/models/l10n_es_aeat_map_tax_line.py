# Copyright 2025 Studio73 - Sergio Martínez <sergio.martinez@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)

from odoo import models


class L10nEsAeatMapTaxLine(models.Model):
    _inherit = "l10n.es.aeat.map.tax.line"

    def get_taxes_for_company(self, company):
        oss_map_lines = self.env.context.get("oss_map_lines", {})
        if self in oss_map_lines:
            oss_taxes_map = self.env.context.get("oss_taxes_map", {})
            return oss_taxes_map.get(self.field_number, {}).get(
                "tax", self.env["account.tax"]
            )
        return super().get_taxes_for_company(company)
