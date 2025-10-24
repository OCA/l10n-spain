# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsAeatMapTaxLine(models.Model):
    _inherit = "l10n.es.aeat.map.tax.line"

    def get_taxes_for_company(self, company):
        self.ensure_one()
        oss_map_lines = [
            self.env.ref("l10n_es_aeat_mod390_oss.aeat_mod390_map_line_126"),
            self.env.ref("l10n_es_aeat_mod390_oss.aeat_mod390_2024_map_line_126"),
        ]
        if self in oss_map_lines:
            return self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", company.id),
                ]
            )
        return super().get_taxes_for_company(company)
