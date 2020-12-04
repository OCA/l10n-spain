# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move am
        SET eu_triangular_deal = ai.eu_triangular_deal
        FROM account_invoice ai
        WHERE ai.id = am.old_invoice_id""",
    )
