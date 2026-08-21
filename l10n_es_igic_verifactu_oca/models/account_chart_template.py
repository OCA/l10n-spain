# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_canary_common", "account.fiscal.position")
    def _get_es_canary_verifactu_fiscal_position(self):
        return self._parse_csv(
            "es_canary_common",
            "account.fiscal.position",
            module="l10n_es_igic_verifactu_oca",
        )
