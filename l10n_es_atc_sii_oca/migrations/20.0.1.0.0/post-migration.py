# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The registration keys of the Canary tax agency that this module added as
records are now codes of the core catalog, and the Spanish data of the IGIC
taxes comes from the chart template override instead of the SII map of the
agency. `l10n_es_aeat_sii_oca` has already migrated the keys of the records by
their code and the data of the taxes used in invoices from the SII map lines,
which is what has been sent."""

import logging

from openupgradelib import openupgrade

from odoo.addons.l10n_es_atc_sii_oca.models.account_chart_template import (
    igic_tax_data,
)

_logger = logging.getLogger(__name__)

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


def _migrate_ignored_igic_tax_data(env):
    """IGIC taxes used in invoices that the SII map of the Canary tax agency
    did not include (5 %, services, retail traders, not subject...): the base
    migration leaves them as 'ignore', as they were not reported. They are
    IGIC taxes the ATC expects in the breakdown, as a new database reports them,
    so they get the data of the template override, or 'sujeto' when it has
    none."""
    tax_data = igic_tax_data()
    env.cr.execute(
        """
        SELECT tax.id, SUBSTRING(imd.name FROM '^[0-9]+_(.*)$')
          FROM account_tax tax
          JOIN ir_model_data imd
            ON imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
         WHERE tax.l10n_es_type = 'ignore'
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$')
               ~ '^account_tax_template_(igic_|[sp]_igic_ns$)'
        """
    )
    changed = []
    for tax_id, template_id in env.cr.fetchall():
        vals = {"l10n_es_type": "sujeto", **tax_data.get(template_id, {})}
        sets = ", ".join(f"{field} = %({field})s" for field in vals)
        env.cr.execute(
            f"UPDATE account_tax SET {sets} WHERE id = %(tax_id)s",
            dict(vals, tax_id=tax_id),
        )
        changed.append(tax_id)
    if changed:
        _logger.warning(
            "IGIC taxes used in invoices and not reported to the SII of the ATC "
            "before, now reported with their IGIC data: %s",
            changed,
        )


@openupgrade.migrate()
def migrate(env, version):
    _migrate_keys(env)
    _migrate_unused_tax_data(env)
    _migrate_ignored_igic_tax_data(env)
