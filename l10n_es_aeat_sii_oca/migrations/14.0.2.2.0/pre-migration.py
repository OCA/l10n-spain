# Copyright 2022 ForgeFlow - Lois Rilo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "res_company", "sii_tax_agency_id"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_company
            SET tax_agency_id = sii_tax_agency_id
            """,
        )
