# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 ForgeFlow, S.L. <contact@forgeflow.com>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import fields, models


class L10nEsVatBookIssuedSummary(models.Model):
    _name = "l10n.es.vat.book.summary"
    _description = "Spanish VAT book summary"
    _order = "book_type, special_tax_group DESC"

    def _selection_special_tax_group(self):
        return self.env["l10n.es.vat.book.line.tax"].fields_get(
            allfields=["special_tax_group"]
        )["special_tax_group"]["selection"]

    vat_book_id = fields.Many2one(comodel_name="l10n.es.vat.book", string="Vat Book id")

    book_type = fields.Selection(
        selection=[("issued", "Issued"), ("received", "Received")], string="Book type"
    )

    base_amount = fields.Float(string="Base amount", readonly="True")

    tax_amount = fields.Float(string="Tax amount", readonly="True")

    total_amount = fields.Float(string="Total amount", readonly="True")
    special_tax_group = fields.Selection(
        selection=_selection_special_tax_group,
        string="Special group",
        help="Special tax group as R.Eq, IRPF, etc",
    )
