# Copyright 20254 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common_mainland", "account.fiscal.position")
    def _get_es_facturae_account_tax(self):
        return self._parse_csv(
            "es_common_mainland",
            "account.fiscal.position",
            module="l10n_es_verifactu_oca",
        )
