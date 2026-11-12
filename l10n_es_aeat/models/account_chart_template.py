# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

from odoo.addons.account.models.chart_template import template

# IGIC purchase taxes of the Spanish chart that Odoo core leaves without
# applicability, while the rest of the IGIC taxes have "03" (Canary Islands).
# Without it they pass for VAT taxes: the SII of the AEAT sends them and the VAT
# prorate applies to them. Temporary fix of the Odoo core data, to remove once
# Odoo core gives them the applicability.
IGIC_TAXES_WITHOUT_APPLICABILITY = [
    *(
        f"account_tax_template_igic_sop_{rate}_s"
        for rate in ("0", "3", "5", "7", "9_5", "15", "20")
    ),
    "account_tax_template_igic_ISP5",
]


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.tax")
    def _get_es_common_account_tax_aeat(self):
        return {
            xml_id: {"l10n_es_applicability": "03"}
            for xml_id in IGIC_TAXES_WITHOUT_APPLICABILITY
        }
