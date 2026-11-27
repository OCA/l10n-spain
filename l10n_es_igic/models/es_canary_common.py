from odoo import models

from odoo.addons.account.models.chart_template import template


class AccountChartTemplate(models.AbstractModel):
    _inherit = "account.chart.template"

    @template("es_canary_common", "account.tax.group")
    def _get_es_igic_account_tax_group_es_canary_common(self):
        return self._parse_csv(
            "es_canary_common", "account.tax.group", module="l10n_es_igic"
        )

    @template(model="account.tax")
    def _get_es_igic_account_tax(self, template_code):
        if "es_canary_common" not in self._get_parent_template(template_code):
            return {}

        tax_data = self._parse_csv(
            "es_canary_common", "account.tax", module="l10n_es_igic"
        )
        self._deref_account_tags(template_code, tax_data)
        return tax_data

    @template("es_canary_common", "account.fiscal.position")
    def _get_es_igic_account_fiscal_position_es_canary_common(self):
        positions = self._parse_csv(
            "es_canary_common", "account.fiscal.position", module="l10n_es_igic"
        )
        # Records are merged by xmlid with a plain dict.update(), which would
        # replace the tax mappings defined by l10n_es: append to them instead.
        base_positions = self._parse_csv(
            "es_canary_common", "account.fiscal.position", module="l10n_es"
        )
        for xmlid, values in positions.items():
            base_taxes = base_positions.get(xmlid, {}).get("tax_ids")
            if base_taxes:
                values["tax_ids"] = base_taxes + values.get("tax_ids", [])
        return positions
