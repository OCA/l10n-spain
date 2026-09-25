# Copyright 2026 Binhex System Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    # The canary chart templates of l10n_es seed `account.asset` models shaped
    # for the standard account_asset module (Enterprise). account_asset_management
    # uses the same model name with a different schema, where `profile_id` is
    # required, so the chart load crashes. See odoo/odoo#286371.
    # Peninsular templates do not seed any asset data, so canary charts behave
    # like them until upstream checks the installed module instead of the model
    # name.

    @template("es_canary_pymes", "account.asset")
    def _get_es_canary_pymes_account_asset(self):
        return {}

    @template("es_canary_full", "account.asset")
    def _get_es_canary_full_account_asset(self):
        return {}

    @template("es_canary_assoc", "account.asset")
    def _get_es_canary_assoc_account_asset(self):
        return {}
