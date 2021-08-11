# Copyright 2021 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book"

    def _prepare_book_line_tax_vals(self, move_line, vat_book_line):
        values = super(L10nEsVatBook, self)._prepare_book_line_tax_vals(
            move_line, vat_book_line
        )
        oss_taxes = self.env["account.tax"].search(
            [("oss_country_id", "!=", False), ("company_id", "=", self.company_id.id)]
        )
        if move_line.tax_line_id in oss_taxes:
            values.update({"tax_amount": 0, "total_amount": values.get("base_amount")})
        return values
