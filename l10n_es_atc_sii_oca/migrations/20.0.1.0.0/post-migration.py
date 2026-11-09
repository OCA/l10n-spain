# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The registration keys of the Canary tax agency that this module added as
records are now codes of the core catalog, and the Spanish data of the IGIC
taxes comes from the chart template override instead of the SII map of the
agency. `l10n_es_aeat_sii_oca` has already migrated the keys of the records by
their code and the data of the taxes used in invoices from the SII map lines,
which is what has been sent."""

from openupgradelib import openupgrade

from odoo.addons.l10n_es_atc_sii_oca.models.account_chart_template import (
    igic_tax_data,
)

KEY_CODES = {
    "aeat_sii_mapping_registration_keys_s_17": "17_igic_sale",
    "aeat_sii_mapping_registration_keys_s_18": "18_igic_sale",
    "aeat_sii_mapping_registration_keys_s_19": "19_igic_sale",
    "aeat_sii_mapping_registration_keys_p_15": "15_igic_purchase",
    "aeat_sii_mapping_registration_keys_p_16": "16_igic_purchase",
    "aeat_sii_mapping_registration_keys_p_17": "17_igic_purchase",
}


def _key_code_sql(column):
    """SQL expression with the new code of the old key record in the column, or
    NULL when it is not one of this module."""
    whens = " ".join(
        f"WHEN '{xml_id}' THEN '{code}'" for xml_id, code in KEY_CODES.items()
    )
    return f"""
        (SELECT CASE imd.name {whens} END
           FROM ir_model_data imd
          WHERE imd.module = 'l10n_es_atc_sii_oca'
            AND imd.model = 'aeat.sii.mapping.registration.keys'
            AND imd.res_id = {column})
    """


def _migrate_keys(env):
    for table, pairs in (
        (
            "account_move",
            (
                ("l10n_es_regime_code", "sii_registration_key"),
                ("l10n_es_regime_code_additional", "sii_registration_key_additional1"),
                (
                    "l10n_es_regime_code_additional2",
                    "sii_registration_key_additional2",
                ),
            ),
        ),
        (
            "account_fiscal_position",
            (
                ("sii_regime_code_sale", "sii_registration_key_sale"),
                ("sii_regime_code_purchase", "sii_registration_key_purchase"),
            ),
        ),
    ):
        for new_column, old_column in pairs:
            if not openupgrade.column_exists(env.cr, table, old_column):
                continue
            new_code = _key_code_sql(f"{table}.{old_column}")
            openupgrade.logged_query(
                env.cr,
                f"""
                UPDATE {table} SET {new_column} = {new_code}
                 WHERE {new_code} IS NOT NULL
                """,
            )


def _migrate_unused_tax_data(env):
    """Data of the IGIC taxes not used in invoices: the one of the template
    (the used ones keep what was sent)."""
    for xml_id, vals in igic_tax_data().items():
        sets = ", ".join(f"{field} = %({field})s" for field in vals)
        env.cr.execute(
            f"""
            UPDATE account_tax tax SET {sets}
              FROM ir_model_data imd
             WHERE imd.module = 'account' AND imd.model = 'account.tax'
               AND imd.res_id = tax.id
               AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') = %(xml_id)s
               AND NOT EXISTS (
                   SELECT 1 FROM account_move_line_account_tax_rel rel
                    WHERE rel.account_tax_id = tax.id)
            """,
            dict(vals, xml_id=xml_id),
        )


@openupgrade.migrate()
def migrate(env, version):
    _migrate_keys(env)
    _migrate_unused_tax_data(env)
