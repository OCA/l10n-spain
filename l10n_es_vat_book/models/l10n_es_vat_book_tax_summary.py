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
    base_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        string="Journal items (Base)",
        relation="account_move_line_l10n_es_vat_book_tax_summary_base_rel",
    )
    move_line_ids = fields.Many2many(
        comodel_name="account.move.line", string="Journal items"
    )

    def view_move_lines_base(self):
        return self.env["l10n.es.aeat.report"]._view_move_lines(self.base_move_line_ids)

    def view_move_lines_tax(self):
        return self.env["l10n.es.aeat.report"]._view_move_lines(self.move_line_ids)
