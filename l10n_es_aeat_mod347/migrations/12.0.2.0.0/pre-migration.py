# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """UPDATE l10n_es_aeat_mod347_move_record
        SET amount = -amount
        WHERE move_type in ('receivable_refund', 'payable_refund')"""
    )
