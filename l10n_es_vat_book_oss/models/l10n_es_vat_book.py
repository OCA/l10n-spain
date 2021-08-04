# Copyright 2021 PESOL (http://pesol.es/)
#                Angel Moya <angel.moya@pesol.es>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsVatBook(models.Model):
    _inherit = 'l10n.es.vat.book'

    def _prepare_book_line_tax_vals(self, move_line, vat_book_line):
        values = super(L10nEsVatBook, self)._prepare_book_line_tax_vals(
            move_line, vat_book_line)
        oss_taxes = self.env['account.tax'].search([
            ('oss_country_id', '!=', False),
        ])
        if move_line.tax_line_id in oss_taxes:
            values.update({'tax_amount': 0,})
        return values
