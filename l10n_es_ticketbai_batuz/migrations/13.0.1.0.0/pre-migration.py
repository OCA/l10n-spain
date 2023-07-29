# Copyright 2023 Bilbonet - Jesus Ramiro
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_table_renames = [
    ("account_invoice_lroe_operation_rel", "old_account_invoice_lroe_operation_rel"),
]


@openupgrade.migrate()
def migrate(env, version):
    cr = env.cr
    openupgrade.rename_tables(cr, _table_renames)
