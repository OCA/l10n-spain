# -*- encoding: utf-8 -*-
# Copyright 2021 PESOL - Angel Moya
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from openerp import api, models


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
        if 126 <= self.env.context.get('field_number', 0) <= 127:
            periods = self.fiscalyear_id.period_ids.filtered(
                lambda x: not x.special)
        if self.env.context.get('field_number', 0) in {123, 126}:
            taxes = self.env['account.tax'].search([
                ("oss_country_id", "!=", False),
                ("company_id", "=", self.company_id.id),
            ])
            codes = (
                taxes.mapped("base_code_id") + taxes.mapped("ref_base_code_id")
            ).mapped("code")
        return super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            codes, periods=periods, include_children=include_children)
