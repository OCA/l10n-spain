# Copyright 2022 ForgeFlow - Lois Rilo
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from openupgradelib import openupgrade


def _get_tax_agency_map(env):
    """Map to move records from aeat.sii.tax.agency to aeat.tax.agency."""
    get_id = env["ir.model.data"]._xmlid_to_res_id
    mig_map = {
        get_id("l10n_es_aeat_sii_oca.aeat_sii_tax_agency_spain"): get_id(
            "l10n_es_aeat.aeat_tax_agency_spain"
        ),
        get_id("l10n_es_aeat_sii_oca.aeat_sii_tax_agency_gipuzkoa"): get_id(
            "l10n_es_aeat.aeat_tax_agency_gipuzkoa"
        ),
        get_id("l10n_es_aeat_sii_oca.aeat_sii_tax_agency_araba"): get_id(
            "l10n_es_aeat.aeat_tax_agency_araba"
        ),
        get_id("l10n_es_aeat_sii_oca.aeat_sii_tax_agency_bizkaia"): get_id(
            "l10n_es_aeat.aeat_tax_agency_bizkaia"
        ),
    }
    return mig_map


def _set_agency_in_company(env, agency_map):
    column_name = openupgrade.get_legacy_name("sii_tax_agency_id")
    default_id = env.ref("l10n_es_aeat.aeat_tax_agency_spain").id
    env.cr.execute(
        """
        SELECT id, %s
        FROM res_company
    """
        % column_name
    )
    res = env.cr.fetchall()
    for company_id, old_sii_agency_id in res:
        new_id = agency_map.get(old_sii_agency_id)
        if new_id:
            openupgrade.logged_query(
                env.cr,
                """
                UPDATE res_company
                SET tax_agency_id = %s
                WHERE id = %s
            """,
                (new_id, company_id),
            )
        if not old_sii_agency_id:
            openupgrade.logged_query(
                env.cr,
                """
                UPDATE res_company
                SET tax_agency_id = %s
                WHERE id = %s
            """,
                (default_id, company_id),
            )


@openupgrade.migrate()
def migrate(env, version):
    agency_map = _get_tax_agency_map(env)
    _set_agency_in_company(env, agency_map)
