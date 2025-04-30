# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    openupgrade.convert_to_company_dependent(
        env, "res.partner", "old_not_in_mod347", "not_in_mod347"
    )
