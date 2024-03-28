# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AeatVatBookMapLines(models.Model):
    _name = "aeat.vat.book.map.line"
    _description = "AEAT Vat Book Map Line"

    def _selection_special_tax_group(self):
        return self.env["l10n.es.vat.book.line.tax"].fields_get(
            allfields=["special_tax_group"]
        )["special_tax_group"]["selection"]

    name = fields.Char()
    book_type = fields.Selection(
        selection=[("issued", "Issued"), ("received", "Received")],
    )
    special_tax_group = fields.Selection(
        selection=_selection_special_tax_group,
        string="Special group",
        help="Special tax group as R.Eq, IRPF, etc",
    )
    fee_type_xlsx_column = fields.Char(string="Type xlsx column")
    fee_amount_xlsx_column = fields.Char(string="Base xlsx column")
    tax_xmlid_ids = fields.Many2many(
        comodel_name="l10n.es.aeat.map.tax.line.tax", string="Taxes"
    )
    account_xmlid_id = fields.Many2one(
        comodel_name="l10n.es.aeat.map.tax.line.account",
        string="Tax Account Restriction",
    )
    tax_agency_ids = fields.Many2many("aeat.tax.agency", string="Tax Agency")

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
        account_id = company._get_account_id_from_xmlid(self.account_xmlid_id.name)
        if account_id:
            account_ids.add(account_id)
        return self.env["account.account"].browse(list(account_ids))
