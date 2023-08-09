# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import ormcache


class AccountTax(models.Model):
    _inherit = "account.tax"

    with_vat_prorate = fields.Boolean(
        compute="_compute_with_vat_prorate", store=True, readonly=False
    )
    prorate_account_ids = fields.Many2many(
        "account.account",
        compute="_compute_with_vat_prorate",
        store=True,
        readonly=True,
        help="Accounts to apply the recompute",
    )
    company_with_vat_prorate = fields.Boolean(
        related="company_id.with_vat_prorate",
        string="Company with VAT prorate",
    )

    @api.depends("company_id.with_vat_prorate")
    def _compute_with_vat_prorate(self):
        for tax in self:
            if tax.company_id.with_vat_prorate:
                tax_template_ids = self.env[
                    "account.tax.template"
                ]._get_vat_prorate_template_xmlids()
                xmlids = self.env["ir.model.data"].search_read(
                    [("model", "=", tax._name), ("res_id", "=", tax.id)],
                    ["name", "module"],
                    limit=1,
                )
                if xmlids:
                    xmlid = xmlids[0]
                    tax_ref = "{}.{}".format(
                        xmlid["module"], xmlid["name"].split("_", 1)[1]
                    )
                    with_vat_prorate = tax_ref in tax_template_ids
                    prorate_account_ids = [(5, 0, 0)]
                    if with_vat_prorate:
                        tax_template = self.env.ref(tax_ref)
                        for (
                            template_account
                        ) in tax_template.prorate_account_template_ids:
                            template_account_xmlids = self.env[
                                "ir.model.data"
                            ].search_read(
                                [
                                    ("model", "=", template_account._name),
                                    ("res_id", "=", template_account.id),
                                ],
                                ["name", "module"],
                                limit=1,
                            )
                            if template_account_xmlids:
                                account = self.env.ref(
                                    "{}.{}_{}".format(
                                        template_account_xmlids[0]["module"],
                                        tax.company_id.id,
                                        template_account_xmlids[0]["name"],
                                    ),
                                    raise_if_not_found=False,
                                )
                                if account:
                                    prorate_account_ids.append((4, account.id))

                    tax.with_vat_prorate = with_vat_prorate
                    tax.prorate_account_ids = prorate_account_ids
                    continue
            tax.with_vat_prorate = False
            tax.prorate_account_ids = False


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    template_with_vat_prorate = fields.Boolean()

    prorate_account_template_ids = fields.Many2many("account.account.template")
    # Name must be different that the account.tax field in order to make it
    # compatible with account_chart_update

    @ormcache()
    def _get_vat_prorate_template_xmlids(self):
        templates = self.env["account.tax.template"].search(
            [("template_with_vat_prorate", "=", True)]
        )
        data = templates._get_external_ids()
        result = []
        for key in data:
            result += data[key]
        return result

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        self.clear_caches()
        return result

    def write(self, vals):
        result = super().write(vals)
        self.clear_caches()
        return result
