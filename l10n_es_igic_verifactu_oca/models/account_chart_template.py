from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_canary_common", "account.fiscal.position")
    def _get_es_common_igic_account_fiscal_position(self):
        return self._parse_csv(
            "es_canary_common",
            "account.fiscal.position",
            module="l10n_es_igic_verifactu_oca",
        )
