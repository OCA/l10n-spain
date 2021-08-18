# Copyright 2021 PESOL - Angel Moya
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    def get_taxes_from_map(self, map_line):
        oss_map_lines = [
            self.env.ref("l10n_es_aeat_mod303_oss.aeat_mod303_202107_map_line_123"),
            self.env.ref("l10n_es_aeat_mod303_oss.aeat_mod303_202107_map_line_126"),
        ]
        if map_line in oss_map_lines:
            return self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", self.company_id.id),
                ]
            )
        return super(L10nEsAeatMod303Report, self).get_taxes_from_map(map_line)
