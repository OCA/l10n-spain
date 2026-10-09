from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    # es_canary_pymes chart
    @template("es_canary_pymes", "account.tax.group")
    def _get_es_canary_pymes_account_tax_group_reav(self):
        return self._parse_csv(
            "es_canary_pymes", "account.tax.group", module="l10n_es_igic_reav"
        )

    @template("es_canary_pymes", "account.tax")
    def _get_es_canary_pymes_account_tax_reav(self):
        additional = self._parse_csv(
            "es_canary_pymes", "account.tax", module="l10n_es_igic_reav"
        )
        return additional

    @template("es_canary_pymes", "account.fiscal.position")
    def _get_es_canary_pymes_account_fiscal_position_reav(self):
        return self._parse_csv(
            "es_canary_pymes", "account.fiscal.position", module="l10n_es_igic_reav"
        )

    # es_canary_full chart
    @template("es_canary_full", "account.tax.group")
    def _get_es_canary_full_account_tax_group_reav(self):
        return self._parse_csv(
            "es_canary_full", "account.tax.group", module="l10n_es_igic_reav"
        )

    @template("es_canary_full", "account.tax")
    def _get_es_canary_full_account_tax_reav(self):
        additional = self._parse_csv(
            "es_canary_full", "account.tax", module="l10n_es_igic_reav"
        )
        return additional

    @template("es_canary_full", "account.fiscal.position")
    def _get_es_canary_full_account_fiscal_position_reav(self):
        return self._parse_csv(
            "es_canary_full", "account.fiscal.position", module="l10n_es_igic_reav"
        )
