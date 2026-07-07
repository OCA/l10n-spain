from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common_mainland", "account.tax.group")
    def _get_es_common_mainland_reav_account_tax_group(self):
        return self._parse_csv(
            "es_common_mainland", "account.tax.group", module="l10n_es_reav"
        )

    @template("es_common_mainland", "account.tax")
    def _get_es_common_mainland_reav_account_tax(self):
        return self._parse_csv(
            "es_common_mainland", "account.tax", module="l10n_es_reav"
        )

    @template("es_common_mainland", "account.fiscal.position")
    def _get_es_common_mainland_reav_account_fiscal_position(self):
        return self._parse_csv(
            "es_common_mainland", "account.fiscal.position", module="l10n_es_reav"
        )
