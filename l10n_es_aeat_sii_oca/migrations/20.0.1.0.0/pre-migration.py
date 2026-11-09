# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # Created empty, so that the ORM does not compute it on every move: the
    # post-migration fills it from the sent registration keys.
    if not openupgrade.column_exists(
        env.cr, "account_move", "l10n_es_regime_code_additional2"
    ):
        openupgrade.logged_query(
            env.cr,
            "ALTER TABLE account_move ADD COLUMN l10n_es_regime_code_additional2 "
            "VARCHAR",
        )
