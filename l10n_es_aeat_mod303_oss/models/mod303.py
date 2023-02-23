# Copyright 2021 PESOL - Angel Moya
# Copyright 2021 FactorLibre - Rodrigo Bonilla <rodrigo.bonilla@factorlibre.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    def get_taxes_from_map(self, map_line):
        oss_map_lines = [
            self.env.ref('l10n_es_aeat_mod303_oss.aeat_mod303_202107_map_line_123'),
            self.env.ref('l10n_es_aeat_mod303_oss.aeat_mod303_202107_map_line_126'),
            self.env.ref('l10n_es_aeat_mod303_oss.aeat_mod303_2023_map_line_123'),
            self.env.ref('l10n_es_aeat_mod303_oss.aeat_mod303_2023_map_line_126'),
        ]
        if map_line in oss_map_lines:
            return self.env['account.tax'].search([
                ('oss_country_id', '!=', False),
                ('company_id', '=', self.company_id.id),
            ])
        return super(L10nEsAeatMod303Report, self).get_taxes_from_map(
            map_line,
        )

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
        return super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            codes, date_start, date_end, map_line,
        )
