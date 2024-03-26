# Copyright 2023 Bilbonet - Jesus Ramiro
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade

_column_renames = {
    "tbai_invoice": [("invoice_id", None), ("cancelled_invoice_id", None)],
    "tbai_invoice_refund_origin": [("account_refund_invoice_id", None)],
}


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(env.cr, _column_renames)
