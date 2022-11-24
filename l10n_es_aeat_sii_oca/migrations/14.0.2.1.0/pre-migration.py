# Copyright 2022 ForgeFlow - Lois Rilo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    # We force a change of name due to a change of model,
    # it will be changed back on post-migration
    openupgrade.rename_xmlids(
        env.cr,
        [
            (
                "l10n_es_aeat_sii_oca.aeat_sii_tax_agency_spain_1_0",
                "l10n_es_aeat_sii_oca.aeat_sii_tax_agency_spain_1_0_old",
            ),
            (
                "l10n_es_aeat_sii_oca.aeat_sii_tax_agency_gipuzkoa_1_0",
                "l10n_es_aeat_sii_oca.aeat_sii_tax_agency_gipuzkoa_1_0_old",
            ),
        ],
    )
    column_name = openupgrade.get_legacy_name("sii_tax_agency_id")
    if not openupgrade.column_exists(env.cr, "res_company", column_name):
        openupgrade.rename_columns(
            env.cr, {"res_company": [("sii_tax_agency_id", column_name)]}
        )
