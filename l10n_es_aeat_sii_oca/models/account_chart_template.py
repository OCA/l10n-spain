from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common_mainland", "account.fiscal.position")
    def _get_es_common_mainland_account_fiscal_position_sii(self):
        return self._parse_csv(
            "es_common_mainland",
            "account.fiscal.position",
            module="l10n_es_aeat_sii_oca",
        )
