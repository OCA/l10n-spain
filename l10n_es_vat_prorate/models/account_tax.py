# Copyright 2022 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_round, ormcache


class AccountTax(models.Model):
    _inherit = "account.tax"

    with_vat_prorate = fields.Boolean(
        compute="_compute_with_vat_prorate", store=True, readonly=False
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
                    tax.with_vat_prorate = (
                        "{}.{}".format(xmlid["module"], xmlid["name"].split("_", 1)[1])
                        in tax_template_ids
                    )
                    continue
            tax.with_vat_prorate = False

    def compute_all(
        self,
        price_unit,
        currency=None,
        quantity=1.0,
        product=None,
        partner=None,
        is_refund=False,
        handle_price_include=True,
    ):
        """If there is a prorate, we will add the new lines here"""
        result = super().compute_all(
            price_unit,
            currency=currency,
            quantity=quantity,
            product=product,
            partner=partner,
            is_refund=is_refund,
            handle_price_include=handle_price_include,
        )
        new_taxes = []
        company = self[:1].company_id or self.env.company
        if not currency:
            currency = company.currency_id
        for tax_val in result["taxes"]:
            tax = self.env["account.tax"].browse(tax_val["id"])
            date = self.env.context.get("vat_prorate_date", False)
            if tax.with_vat_prorate and tax_val["account_id"] and date:
                prec = currency.rounding
                prorate = self.company_id.get_prorate(date)
                new_vals = tax_val.copy()
                new_vals["vat_prorate"] = True
                tax_val["amount"] = float_round(
                    tax_val["amount"] * (prorate / 100), precision_rounding=prec
                )
                new_vals["amount"] -= tax_val["amount"]
                result["total_void"] += new_vals["amount"]
                new_taxes.append(new_vals)
        result["taxes"] += new_taxes
        return result


class AccountTaxTemplate(models.Model):
    _inherit = "account.tax.template"

    template_with_vat_prorate = fields.Boolean()
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
    def create(self, mvals):
        result = super(AccountTaxTemplate, self).create(mvals)
        self.clear_caches()
        return result

    def write(self, vals):
        result = super().write(vals)
        self.clear_caches()
        return result
