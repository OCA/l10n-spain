# Copyright 2022 Sygel - Manuel Regidor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsAeatMod390Report(models.Model):
    _inherit = "l10n.es.aeat.mod390.report"

    def get_taxes_from_map(self, map_line):
        oss_map_lines = [
            self.env.ref("l10n_es_aeat_mod390_oss.aeat_mod390_map_line_126"),
        ]
        if map_line in oss_map_lines:
            return self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        return super().get_taxes_from_map(map_line)
