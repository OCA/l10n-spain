# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class L10nEsAeatMod303Report(models.Model):
    _inherit = 'l10n.es.aeat.mod303.report'

    def _default_cash_basis_receivable(self):
        return bool(self.env['account.tax'].search_count([
            ('company_id', '=', self._default_company_id().id),
            ('type_tax_use', '=', 'sale'),
            ('use_cash_basis', '=', True),
        ]))

    def _default_cash_basis_payable(self):
        return bool(self.env['account.tax'].search_count([
            ('company_id', '=', self._default_company_id().id),
            ('type_tax_use', '=', 'purchase'),
            ('use_cash_basis', '=', True),
        ]))

    cash_basis_receivable = fields.Boolean(
        string="Cash basis for sales",
        default=_default_cash_basis_receivable,
    )
    cash_basis_payable = fields.Boolean(
        string="Cash basis for purchases",
        default=_default_cash_basis_payable,
    )

    def _get_move_line_domain(self, codes, date_start, date_end, map_line):
        """Add the possibility of getting move lines from moves generated
        from cash basis reconciliations so that the amounts appear on the
        payment date.
        """
        domain = super(L10nEsAeatMod303Report, self)._get_move_line_domain(
            codes, date_start, date_end, map_line,
        )
        for i, element in enumerate(domain):
            if element[0] == 'move_id.move_type':
                domain[i:i] = [
                    '|',
                    ('move_id.tax_cash_basis_rec_id', '!=', False),
                ]
                break
        return domain
