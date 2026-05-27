# Copyright 2026 Tecnativa - Christian Ramos
# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import models


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book"

    def _calculate_vat_book(self):
        return super(
            L10nEsVatBook, self.with_context(calculate_vat_book=True)
        )._calculate_vat_book()
