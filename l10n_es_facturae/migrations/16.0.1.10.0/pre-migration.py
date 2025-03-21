# Copyright 2025 Dixmit
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if not openupgrade.column_exists(
        env.cr, "account_move", "facturae_withheld_amount"
    ):
        # Avoid computation of the field
        openupgrade.add_fields(
            env,
            [
                (
                    "facturae_withheld_amount",
                    "account.move",
                    "account_move",
                    "float",
                    "numeric",
                    "l10n_es_facturae",
                    0.0,
                )
            ],
        )
