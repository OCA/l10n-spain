# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.tax.group")
    def _get_es_canon_account_tax_group(self):
        return self._parse_csv(
            "es_common", "account.tax.group", module="l10n_es_digital_canon"
        )

    @template("es_common", "account.tax")
    def _get_es_canon_account_tax(self):
        return self._parse_csv(
            "es_common", "account.tax", module="l10n_es_digital_canon"
        )

    def _load_data(self, data):
        """When loading digital canon taxes, they must have a lower sequence
        than all other taxes so that subsequent taxes can be calculated.
        """
        result = super()._load_data(data)
        if "account.tax" not in result:
            return result
        # Get all canon digital tax groups
        canon_groups = self.env["account.tax.group"].search(
            [("name", "=like", "Canon digital%")]
        )
        if not canon_groups:
            return result
        result["account.tax"].filtered(lambda t: t.tax_group_id in canon_groups).write(
            {"sequence": -10}
        )
        return result
