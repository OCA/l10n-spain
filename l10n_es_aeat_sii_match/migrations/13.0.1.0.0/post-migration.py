# Copyright 2023 Studio73 - Carlos Reyes <carlos@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade
from psycopg2.extensions import AsIs


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "account_move", "old_invoice_id"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE l10n_es_aeat_sii_match_result
            SET invoice_id = am.id
            FROM account_move am
            WHERE %s = am.old_invoice_id""",
            (AsIs(openupgrade.get_legacy_name("invoice_id")),),
        )
