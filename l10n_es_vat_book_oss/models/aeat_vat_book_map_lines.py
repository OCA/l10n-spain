# Copyright 2021 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AeatVatBookMapLines(models.Model):
    _inherit = "aeat.vat.book.map.line"

    def get_taxes(self, report):
        self.ensure_one()
        s_iva_map_line = self.env.ref("l10n_es_vat_book.aeat_vat_book_map_line_s_iva")
        taxes = super().get_taxes(report)
        if s_iva_map_line == self:
            taxes += self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", report.company_id.id),
                ]
            )
        return taxes
