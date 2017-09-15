# -*- coding: utf-8 -*-
# Copyright Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate(use_env=True)
def migrate(env, version):
    """Move the invoice sequence of the refund journal to the
    refund sequence of the target journal where it has been merged.
    """
    column_name = openupgrade.get_legacy_name('merged_journal_id')
    if not openupgrade.column_exists(env.cr, 'account_journal', column_name):
        # Avoid to crash if the column doesn't exist
        return
    openupgrade.logged_query(
        env.cr,
        """UPDATE account_journal aj
        SET refund_inv_sequence_id = aj2.invoice_sequence_id
        FROM account_journal aj2
        WHERE aj2.%s = aj.id
        """ % column_name
    )
