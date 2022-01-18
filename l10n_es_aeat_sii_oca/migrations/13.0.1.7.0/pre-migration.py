# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_column_renames = {
    "account_move": [
        ("sii_thirdparty_invoice", "thirdparty_invoice"),
        ("sii_thirdparty_number", "thirdparty_number"),
    ]
}


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "account_move", "sii_thirdparty_invoice"):
        openupgrade.rename_columns(env.cr, _column_renames)
