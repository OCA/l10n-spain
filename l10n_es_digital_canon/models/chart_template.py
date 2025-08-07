# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import models
from odoo.tools import config


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    def _generate_tax(
        self, company, accounts_exist=False, existing_template_to_tax=None
    ):
        """When loading digital canon taxes, they must have a lower sequence
        than all other taxes so that subsequent taxes can be calculated.

        This is applied both when the chart of accounts is initially loaded
        and when it is updated using account_chart_update.
        """
        res = super()._generate_tax(company, accounts_exist, existing_template_to_tax)
        if config["test_enable"]:
            return res
        if (
            company.chart_template_id.get_external_id()[
                company.chart_template_id.id
            ].split(".")[0]
            == "l10n_es"
        ):
            tax_group = self.env.ref(
                "l10n_es_digital_canon.tax_group_digital_canon_template",
                raise_if_not_found=False,
            )
            if tax_group:
                taxes = self.env["account.tax"].search(
                    [
                        ("tax_group_id", "=", tax_group.id),
                        ("company_id", "=", company.id),
                    ]
                )
                for tax in taxes:
                    tax.write({"sequence": -10})
        return res
