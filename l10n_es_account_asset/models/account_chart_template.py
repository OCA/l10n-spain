# Copyright 2026 Binhex System Solutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    def _is_oca_asset_management(self):
        """Whether the asset models are the ones of OCA's account_asset_management.

        account_asset_management replaces the standard account_asset module with a
        different schema, where `profile_id` is required, so the asset models seeded
        by the canary templates cannot be created. See odoo/odoo#286371. Probing
        `"profile_id" in self.env["account.asset"]._fields` would be an equivalent
        check, tied even more closely to the data the templates carry.
        """
        return "account.asset.profile" in self.env

    @template("es_canary_pymes", "account.asset")
    def _get_es_canary_pymes_account_asset(self):
        if self._is_oca_asset_management():
            return {}
        return super()._get_es_canary_pymes_account_asset()

    @template("es_canary_full", "account.asset")
    def _get_es_canary_full_account_asset(self):
        if self._is_oca_asset_management():
            return {}
        return super()._get_es_canary_full_account_asset()

    @template("es_canary_assoc", "account.asset")
    def _get_es_canary_assoc_account_asset(self):
        if self._is_oca_asset_management():
            return {}
        return super()._get_es_canary_assoc_account_asset()
