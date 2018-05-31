# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo.osv.expression import normalize_domain, AND, OR


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

    @api.model
    def _get_tax_lines(self, codes, date_start, date_end, map_line):
        """Hide cash basis lines that are payment entries for the same period
        of their counterpart, for not declaring twice the amount.
        """
        AccountMove = self.env['account.move']
        move_lines = super(L10nEsAeatMod303Report, self)._get_tax_lines(
            codes, date_start, date_end, map_line,
        )
        if map_line.field_number in [62, 63, 74, 75]:
            new_lines = self.env['account.move.line']
            for line in move_lines:
                recs = (
                    line.move_id.mapped('line_ids.matched_debit_ids') +
                    line.move_id.mapped('line_ids.matched_credit_ids')
                )
                other_move = AccountMove.search([
                    ('tax_cash_basis_rec_id', 'in', recs.ids),
                ], limit=1)
                if (not other_move or other_move.date < date_start or
                        other_move.date > date_end):
                    new_lines += line
            move_lines = new_lines
        return move_lines

    def _get_move_line_domain(self, codes, date_start, date_end, map_line):
        """Add the possibility of getting move lines from moves generated
        from cash basis reconciliations so that the amounts appear on the
        payment date. This is needed as the cash basis move is not of the
        expected move type.

        Also adjust domains for the special case of 12% VAT for farming.
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
        if map_line.field_number == 42:
            # Exclude here the VAT that is used as base for IRPF 2%, as it
            # has the tax_exigible field marked.
            domain += [
                ('tax_ids', '=', False),
            ]
        elif map_line.field_number == 75:
            # And add it here
            domain_mandatory = []
            domain_optional = []
            domain_extra = []
            for i, element in enumerate(domain):
                if element[0] == 'date' and element[1] == '<=':
                    domain_mandatory = normalize_domain(domain[:i+1])
                    domain_optional = normalize_domain(domain[i+1:])
                    domain_extra = [
                        '&',
                        ('tax_ids', '!=', False),
                        ('tax_line_id.description', '=', 'P_IVA12_AGR'),
                    ]
                    break
            domain = AND(
                [domain_mandatory] + [OR([domain_extra, domain_optional])]
            )
        return domain
