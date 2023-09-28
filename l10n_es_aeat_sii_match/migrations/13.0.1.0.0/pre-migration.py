# Copyright 2023 Studio73 - Carlos Reyes <carlos@studio73.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.lift_constraints(env.cr, "l10n_es_aeat_sii_match_result", "invoice_id")
    openupgrade.rename_columns(
        env.cr, {"l10n_es_aeat_sii_match_result": [("invoice_id", None)]}
    )
