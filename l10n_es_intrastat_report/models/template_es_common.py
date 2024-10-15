# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", model="account.fiscal.position")
    def _get_fiscal_position(self):
        return {
            "fp_intra_private": {"intrastat": "b2c"},
            "fp_intra": {"intrastat": "b2b"},
        }
