# Copyright 2023 Digital5 - Enrique Martin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade
from psycopg2 import sql


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
        UPDATE tbai_invoice_refund_origin
        SET expedition_date = TO_DATE({}, 'DD-MM-YYYY')
        """
        ).format(sql.Identifier(openupgrade.get_legacy_name("expedition_date"))),
    )
