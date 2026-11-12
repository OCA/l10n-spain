from odoo import models

from odoo.addons.account.models.chart_template import template

# Taxes of the Odoo core chart that the REAV fiscal position keeps as they are
# (art. 146 LIVA): the investment goods of the agency keep their normal
# deduction, and its own exempt supplies are outside the special regime. Since
# 19.0 a tax with fiscal positions that the position doesn't replace is removed
# from the invoice unless the position is one of them (`map_tax`).
REAV_KEPT_TAXES = (
    "account_tax_template_p_iva4_bi",
    "account_tax_template_p_iva5_bi",
    "account_tax_template_p_iva10_bi",
    "account_tax_template_p_iva21_bi",
    "account_tax_template_s_iva0",
    "account_tax_template_s_iva0_art22",
    "account_tax_template_s_iva0_art23",
    "account_tax_template_s_iva0_nsd",
)


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_common", "account.tax.group")
    def _get_es_common_reav_account_tax_group(self):
        return self._parse_csv("es_common", "account.tax.group", module="l10n_es_reav")

    @template("es_common", "account.tax")
    def _get_es_common_reav_account_tax(self):
        taxes = self._parse_csv("es_common", "account.tax", module="l10n_es_reav")
        # The values of a template function replace the previous ones, so the
        # REAV position is added to the fiscal positions of the Odoo core chart
        core_taxes = self._parse_csv("es_common", "account.tax", module="l10n_es")
        for xmlid in REAV_KEPT_TAXES:
            positions = core_taxes.get(xmlid, {}).get("fiscal_position_ids")
            if positions:
                taxes[xmlid] = {"fiscal_position_ids": f"{positions},fp_reav"}
        return taxes

    @template("es_common", "account.fiscal.position")
    def _get_es_common_reav_account_fiscal_position(self):
        return self._parse_csv(
            "es_common", "account.fiscal.position", module="l10n_es_reav"
        )
