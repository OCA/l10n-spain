from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.tax.group")
    def _get_es_dua_account_tax_group(self):
        return self._parse_csv("es_common", "account.tax.group", module="l10n_es_dua")

    @template("es_common", "account.tax")
    def _get_es_dua_account_tax(self):
        return self._parse_csv("es_common", "account.tax", module="l10n_es_dua")

    @template("es_common", "account.fiscal.position")
    def _get_es_dua_account_fiscal_position(self):
        return self._parse_csv(
            "es_common", "account.fiscal.position", module="l10n_es_dua"
        )
