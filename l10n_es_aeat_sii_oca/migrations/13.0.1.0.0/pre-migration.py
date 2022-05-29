# Copyright 2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Pre-create columns for avoiding triggering the compute method
    openupgrade.logged_query(
        env.cr, "ALTER TABLE account_move ADD sii_description text"
    )
    openupgrade.add_fields(
        env,
        [
            (
                "thirdparty_invoice",
                "account.move",
                "account_move",
                "boolean",
                False,
                "l10n_es_aeat_sii_oca",
                False,
            ),
        ],
    )
