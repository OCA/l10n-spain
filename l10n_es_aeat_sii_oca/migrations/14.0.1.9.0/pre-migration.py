# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

from odoo.tools.sql import column_exists

_column_renames = {
    "account_move": [
        ("sii_thirdparty_invoice", "thirdparty_invoice"),
        ("sii_thirdparty_number", "thirdparty_number"),
    ]
}


@openupgrade.migrate()
def migrate(env, version):
    if column_exists(env.cr, "account_move", "sii_thirdparty_invoice"):
        openupgrade.rename_columns(env.cr, _column_renames)
