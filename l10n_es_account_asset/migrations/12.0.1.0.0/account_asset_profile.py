# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade
from psycopg2 import sql


@openupgrade.migrate()
def migrate(env, version):
    for table in {'account_asset_profile', 'account_asset'}:
        openupgrade.logged_query(
            env.cr, sql.SQL(
                """
                UPDATE {}
                SET method_time = 'percentage'
                WHERE {} = 'percentage'"""
            ).format(
                sql.Identifier(table),
                sql.Identifier(openupgrade.get_legacy_name('method_time')),
            )
        )
