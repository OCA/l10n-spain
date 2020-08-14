# Copyright 2018 Comunitea - Omar Castiñeira <omar@comunitea.com>
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    base_company = fields.Monetary(
        string='Base in company currency',
        compute="_compute_base_amount_company",
    )
    amount_company = fields.Monetary(
        string='Amount in company currency',
        compute="_compute_base_amount_company",
    )

    def _compute_base_amount_company(self):
        for tax in self:
            if (tax.invoice_id.currency_id !=
                    tax.invoice_id.company_id.currency_id):
                rate_date = (
                    tax.invoice_id._get_currency_rate_date() or
                    fields.Date.today()
                )
                currency = tax.invoice_id.currency_id
                company = tax.invoice_id.company_id
                tax.base_company = currency._convert(
                    tax.base, company.currency_id, company, rate_date)
                tax.amount_company = currency._convert(
                    tax.amount, company.currency_id, company, rate_date)
            else:
                tax.base_company = tax.base
                tax.amount_company = tax.amount
