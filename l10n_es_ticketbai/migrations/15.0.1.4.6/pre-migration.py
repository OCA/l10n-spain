# Copyright 2023 Digital5 - Enrique Martin
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_columns(
        env.cr, {"tbai_invoice_refund_origin": [("expedition_date", None)]}
    )
