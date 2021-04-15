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

    name = fields.Char(
        string="Name",
    )
    book_type = fields.Selection(
        selection=[("issued", "Issued"), ("received", "Received")],
        string="Book type",
    )
    special_tax_group = fields.Selection(
        selection=_selection_special_tax_group,
        string="Special group",
        help="Special tax group as R.Eq, IRPF, etc",
    )
    fee_type_xlsx_column = fields.Char(string="Type xlsx column")
    fee_amount_xlsx_column = fields.Char(string="Base xlsx column")
    tax_tmpl_ids = fields.Many2many(
        comodel_name="account.tax.template",
        string="Taxes",
    )
    tax_account_id = fields.Many2one(
        comodel_name="account.account.template",
        string="Tax Account Restriction",
    )
