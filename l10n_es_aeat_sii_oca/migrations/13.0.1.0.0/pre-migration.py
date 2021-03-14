# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Pre-create column for avoiding triggering the compute method
    openupgrade.logged_query(
        env.cr, "ALTER TABLE account_move ADD sii_description text"
    )
