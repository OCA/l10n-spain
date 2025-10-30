# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(env.cr, "res_partner", "old_not_in_mod347_17"):
        return  # Already migrated in 16
    env = api.Environment(env.cr, SUPERUSER_ID, {})
    openupgrade.convert_to_company_dependent(
        env, "res.partner", "old_not_in_mod347_17", "not_in_mod347"
    )
