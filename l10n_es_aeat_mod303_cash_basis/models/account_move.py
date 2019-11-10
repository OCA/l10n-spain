# Copyright 2018 Comunitea - Santi Argüeso
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    move_type_cash_basis = fields.Selection(
        string="Move type RECC", selection=[
            ('other', 'Other'),
            ('receivable', 'Receivable'),
            ('receivable_refund', 'Receivable refund'),
            ('payable', 'Payable'),
            ('payable_refund', 'Payable refund'),
        ], readonly=True)

    def _store_move_type_cash_basis(self):
        for move in self:
            rec = move.tax_cash_basis_rec_id
            move_type = 'other'
            if rec:
                invoice = rec.debit_move_id.invoice_id or \
                    rec.credit_move_id.invoice_id
                if invoice:
                    move_type = invoice.move_id.move_type
            move.move_type_cash_basis = move_type

    @api.multi
    def reverse_moves(self, date=None, journal_id=None):
        reversed_move_ids = super(AccountMove, self).reverse_moves(date,
                                                                   journal_id)
        reversed_moves = self.browse(reversed_move_ids)
        reverse_types = {
            'receivable': 'receivable_refund',
            'receivable_refund': 'receivable',
            'payable': 'payable_refund',
            'payable_refund': 'payable',
        }
        for move in reversed_moves:
            if move.move_type_cash_basis in reverse_types.keys():
                move.move_type_cash_basis = reverse_types[
                    move.move_type_cash_basis]
        return reversed_moves.mapped('id')
