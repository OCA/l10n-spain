# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class AccountPartialReconcileCashBasis(models.Model):
    _inherit = 'account.partial.reconcile'

    def create_tax_cash_basis_entry(self, value_before_reconciliation):
        """Modify tax_exigible and tax values before reconciliation for
        the special case of 12% VAT for farming, as its value is included in
        IRPF 2%.

        This way, we trick standard cash basis system for generating proper
        payment accounting moves.
        """
        moves = self.debit_move_id.move_id + self.credit_move_id.move_id
        tax_lines = self.env['account.move.line']
        base_lines = {}
        for line in moves.mapped('line_ids'):
            if 'P_IRPF2' in line.tax_ids.mapped('description'):
                base_lines[line.tax_ids] = line
                if (line.tax_line_id.description == 'P_IVA12_AGR' and
                        line.tax_exigible):
                    tax_lines += line
        if tax_lines:
            tax_lines.write({'tax_exigible': False})
        for line in base_lines.values():
            line.tax_ids = [
                (3, x.id) for x in
                line.tax_ids.filtered(lambda l: l.description == 'P_IRPF2')
            ]
        res = super(
            AccountPartialReconcileCashBasis, self,
        ).create_tax_cash_basis_entry(value_before_reconciliation)
        if tax_lines:
            tax_lines.write({'tax_exigible': True})
        for taxes, line in base_lines.items():
            line.tax_ids = [(6, 0, taxes.ids)]
        return res
