# Copyright 2021 PESOL - Angel Moya
# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    def _get_tax_lines(self, codes, date_start, date_end, map_line):
        """Don't populate results for fields 126-127 for reports different from
        last of the year one or when not exonerated of presenting model 390.
        """
        res = super(L10nEsAeatMod303Report, self)._get_tax_lines(
            codes, date_start, date_end, map_line)
        if 126 <= map_line.field_number <= 127:
            if (self.exonerated_390 == '2' or not self.has_operation_volume
                    or self.period_type not in ('4T', '12')):
                return self.env['account.move.line']
        return res

    def _get_move_line_domain(self, codes, date_start, date_end, map_line):
        """Changes dates to full year when the summary on last report of the
        year for the corresponding fields. Only field number is checked as
        the complete check for not bringing results is done on
        `_get_tax_lines`.
        """
        if 126 <= map_line.field_number <= 127:
            date_start = date_start[:4] + '-01-01'
            date_end = date_end[:4] + '-12-31'
        if map_line.field_number in [123, 126]:
            taxes = self.env['account.tax'].search([
                ("oss_country_id", "!=", False),
                ("company_id", "=", self.company_id.id),
            ])
            codes = taxes.mapped("description")
        return super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            codes, date_start, date_end, map_line,
        )
