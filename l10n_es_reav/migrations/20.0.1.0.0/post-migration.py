# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """The REAV taxes get the travel agencies regime code (key 05 of the SII and
    VERI*FACTU) and the VAT applicability of the chart template, which a chart
    reload does not write on existing taxes."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax tax
           SET l10n_es_regime_code = COALESCE(tax.l10n_es_regime_code, '05'),
               l10n_es_applicability = COALESCE(tax.l10n_es_applicability, '01')
          FROM ir_model_data imd
         WHERE imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') IN (
               'account_tax_template_p_reav0', 'account_tax_template_s_reav0'
           )
        """,
    )
