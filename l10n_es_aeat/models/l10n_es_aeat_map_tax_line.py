# Copyright 2013-2018 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import fields, models


class L10nEsAeatMapTaxLine(models.Model):
    _name = "l10n.es.aeat.map.tax.line"
    _order = "field_number asc, id asc"
    _description = "AEAT tax mapping line"

    field_number = fields.Integer(required=True)
    tax_xmlid_ids = fields.Many2many(
        comodel_name="l10n.es.aeat.map.tax.line.tax", string="Taxes templates"
    )
    account_xmlid_ids = fields.Many2many(
        comodel_name="l10n.es.aeat.map.tax.line.account",
        string="Account Template",
    )
    name = fields.Char(required=True)
    map_parent_id = fields.Many2one(comodel_name="l10n.es.aeat.map.tax", required=True)
    move_type = fields.Selection(
        selection=[("all", "All"), ("regular", "Regular"), ("refund", "Refund")],
        string="Operation type",
        default="all",
        required=True,
    )
    field_type = fields.Selection(
        selection=[("base", "Base"), ("amount", "Amount"), ("both", "Both")],
        default="amount",
        required=True,
    )
    sum_type = fields.Selection(
        selection=[
            ("credit", "Credit"),
            ("debit", "Debit"),
            ("both", "Both (Credit - Debit)"),
        ],
        string="Summarize type",
        default="both",
        required=True,
    )
    exigible_type = fields.Selection(
        selection=[
            ("yes", "Only exigible amounts"),
            ("no", "Only non-exigible amounts"),
            ("both", "Both exigible and non-exigible amounts"),
        ],
        required=True,
        string="Exigibility",
        default="yes",
    )
    inverse = fields.Boolean(string="Inverse summarize sign", default=False)
    to_regularize = fields.Boolean()

    def get_taxes_for_company(self, company):
        """Obtain the taxes corresponding to this line according the given company."""
        self.ensure_one()
        tax_ids = set()
        for tax_xmlid in self.tax_xmlid_ids:
            tax_id = company._get_tax_id_from_xmlid(tax_xmlid.name)
            if tax_id:
                tax_ids.add(tax_id)
        return self.env["account.tax"].browse(list(tax_ids))

    def get_accounts_for_company(self, company):
        """Obtain the accounts corresponding to the line according the given company."""
        self.ensure_one()
        account_ids = set()
        for account_xmlid in self.account_xmlid_ids:
            account_id = company._get_account_id_from_xmlid(account_xmlid.name)
            if account_id:
                account_ids.add(account_id)
        return self.env["account.account"].browse(list(account_ids))


class L10nEsAeatMapTaxLineTax(models.Model):
    _name = "l10n.es.aeat.map.tax.line.tax"
    _order = "name, id"
    _description = "AEAT tax mapping line - Tax"

    name = fields.Char()


class L10nEsAeatMapTaxLineAccount(models.Model):
    _name = "l10n.es.aeat.map.tax.line.account"
    _order = "name, id"
    _description = "AEAT tax mapping line - Account"

    name = fields.Char()
