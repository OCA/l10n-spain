# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

from odoo.addons.l10n_es_aeat.models.account_chart_template import (
    IGIC_TAXES_WITHOUT_APPLICABILITY,
)


@openupgrade.migrate()
def migrate(env, version):
    """The IGIC taxes that Odoo core leaves without applicability get the one of
    the Canary Islands (see the chart template override), unless the user has
    already given them one."""
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE account_tax tax SET l10n_es_applicability = '03'
          FROM ir_model_data imd
         WHERE imd.module = 'account' AND imd.model = 'account.tax'
           AND imd.res_id = tax.id
           AND SUBSTRING(imd.name FROM '^[0-9]+_(.*)$') IN %s
           AND tax.l10n_es_applicability IS NULL
        """,
        (tuple(IGIC_TAXES_WITHOUT_APPLICABILITY),),
    )
