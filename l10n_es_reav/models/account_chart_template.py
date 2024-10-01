from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    # es_common chart
    @template("es_common", "account.tax.group")
    def _get_es_common_account_tax_group(self):
        return self._parse_csv("es_common", "account.tax.group", module="l10n_es_reav")

    @template("es_common", "account.tax")
    def _get_es_common_account_tax(self):
        additional = self._parse_csv("es_common", "account.tax", module="l10n_es_reav")
        return additional

    @template("es_common", "account.fiscal.position")
    def _get_es_common_account_fiscal_position(self):
        return self._parse_csv(
            "es_common", "account.fiscal.position", module="l10n_es_reav"
        )
