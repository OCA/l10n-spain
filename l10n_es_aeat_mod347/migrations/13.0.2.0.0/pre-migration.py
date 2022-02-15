# Copyright 2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.tools.sql import column_exists


def migrate(cr, version):
    if not column_exists(cr, "l10n_es_aeat_mod347_move_record", "move_type"):
        return  # migration directly from v12
    cr.execute(
        """UPDATE l10n_es_aeat_mod347_move_record
        SET amount = -amount
        WHERE move_type in ('receivable_refund', 'payable_refund')"""
    )
