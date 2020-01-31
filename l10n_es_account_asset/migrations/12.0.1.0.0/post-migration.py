# Copyright 2019-2020 Tecnativa - Pedro M. Baeza
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
        openupgrade.logged_query(
            env.cr, sql.SQL(
                """
                UPDATE {table}
                SET annual_percentage = method_percentage * 12 / {field}
                WHERE annual_percentage != (method_percentage * 12 / {field})
                    AND method_time = 'percentage'
                """
            ).format(
                table=sql.Identifier(table),
                field=sql.Identifier(
                    openupgrade.get_legacy_name('method_period')),
            )
        )
