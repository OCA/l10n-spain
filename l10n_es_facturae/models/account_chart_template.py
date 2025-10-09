from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common_mainland", "account.tax")
    def _get_es_mainland_facturae_account_tax(self):
        return self._parse_csv(
            "es_common_mainland", "account.tax", module="l10n_es_facturae"
        )

    @template("es_canary_common", "account.tax")
    def _get_es_canary_facturae_account_tax(self):
        return self._parse_csv(
            "es_canary_common", "account.tax", module="l10n_es_facturae"
        )
