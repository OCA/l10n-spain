# Copyright 2021 Tecnativa - João Marques
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from psycopg2 import sql


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
            UPDATE pos_order
            SET pos_reference = l10n_es_unique_id,
            l10n_es_unique_id = pos_reference
        """
        ),
    )
