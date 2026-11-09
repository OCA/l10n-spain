from odoo import models

from odoo.addons.account.models.chart_template import template

class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.fiscal.position")
    def _get_es_common_account_fiscal_position_sii(self):
        return self._parse_csv(
            "es_common",
            "account.fiscal.position",
            module="l10n_es_aeat_sii_oca",
        )

    @template("es_common", "account.tax")
    def _get_es_common_account_tax_sii(self):
        # Services to non-EU customers are not subject (location rules), not
        # exports: with the export key 02 the AEAT rejects an invoice of only
        # those services (error 1252) and one that mixes them with exported
        # goods needs 01 + 02 (https://github.com/odoo/odoo/pull/301554).
        return {"account_tax_template_s_iva_e": {"l10n_es_regime_code": False}}
