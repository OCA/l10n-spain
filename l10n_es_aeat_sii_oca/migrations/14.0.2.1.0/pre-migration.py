# Copyright 2022 ForgeFlow - Lois Rilo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    column_name = openupgrade.get_legacy_name("sii_tax_agency_id")
    if not openupgrade.column_exists(env.cr, "res_company", column_name):
        openupgrade.rename_columns(
            env.cr, {"res_company": [("sii_tax_agency_id", column_name)]}
        )
