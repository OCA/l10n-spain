# Copyright 2017 Praxya (http://praxya.com/)
#                Daniel Rodriguez Lijo <drl.9319@gmail.com>
# Copyright 2017 ForgeFlow, S.L. <contact@forgeflow.com>
# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import fields, models


class L10nEsVatBookIssuedTaxSummary(models.Model):
    _name = "l10n.es.vat.book.tax.summary"
    _description = "Spanish VAT book tax summary"
    _inherit = "l10n.es.vat.book.summary"

    _order = "book_type, special_tax_group DESC, tax_id"

    tax_id = fields.Many2one(
        comodel_name="account.tax",
        string="Account Tax",
        required=True,
        ondelete="cascade",
    )
