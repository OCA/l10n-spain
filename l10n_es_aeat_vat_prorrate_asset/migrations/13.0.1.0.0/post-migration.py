# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_move_line aml
        SET vat_prorrate_percent = ail.vat_prorrate_percent
        FROM account_invoice_line ail
        WHERE ail.id = aml.old_invoice_line_id
        AND ail.vat_prorrate_percent > 0""",
    )
