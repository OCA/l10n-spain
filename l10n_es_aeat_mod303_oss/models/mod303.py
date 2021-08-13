# -*- encoding: utf-8 -*-
# Copyright 2021 PESOL - Angel Moya
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from openerp import api, fields, models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    @api.multi
    def _get_tax_code_lines(self, codes, periods=None, include_children=True):
        """Don't populate results for fields 126-127 for reports different from
        last of the year one or when not exonerated of presenting model 390.
        """
        if 126 <= self.env.context.get('field_number', 0) <= 127:
            if (self.exonerated_390 == '2' or not self.has_operation_volume
                    or self.period_type not in ('4T', '12')):
                return self.env['account.move.line']
        return super(L10nEsAeatMod303Report, self)._get_tax_code_lines(
            codes, periods=periods, include_children=include_children,
        )

    @api.multi
    def _get_move_line_domain(
            self, codes, periods=None, include_children=True):
        oss_map_lines = [123, 126]
        if 126 <= self.env.context.get('field_number', 0) <= 127:
            fiscalyear_code = fields.Date.from_string(
                periods[:1].date_stop
            ).year
            date_start = "%s-01-01" % fiscalyear_code
            date_stop = "%s-12-31" % fiscalyear_code
            periods = self.env["account.period"].search([
                ('date_start', '>=', date_start),
                ('date_stop', '<=', date_stop),
                ('special', '=', False)
            ])
        res = super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            codes, periods=periods, include_children=include_children)
        if self.env.context.get('field_number', 0) in oss_map_lines:
            tax_codes = self.env['account.tax.code'].search([
                ('oss_country_id', '!=', False),
                ('code', 'like', 'OSSEU__TB%'),
                ('company_id', '=', self.company_id.id),
            ])
            new_tax_code_id = None
            tax_code_id_del = None
            for x in res:
                if x[0] == 'tax_code_id':
                    new_tax_code_id = ('tax_code_id', 'child_of', tax_codes.ids)
                    tax_code_id_del = x
                    break
            if tax_code_id_del:
                res.remove(tax_code_id_del)
                res.append(new_tax_code_id)
        return res
