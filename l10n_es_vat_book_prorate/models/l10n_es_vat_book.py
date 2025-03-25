# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

from odoo import models


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book"

    def _get_move_lines_with_taxes(self, move_lines, taxes, accounts):
        lines = super()._get_move_lines_with_taxes(move_lines, taxes, accounts)
        lines |= move_lines.filtered(
            lambda line: line.vat_prorate and line.tax_line_id & taxes
        )
        return lines

    def _prepare_book_line_tax_vals(self, move_line, vat_book_line):
        vals = super()._prepare_book_line_tax_vals(move_line, vat_book_line)
        if move_line.vat_prorate:
            vals["deductible_amount"] = 0.0
        return vals
