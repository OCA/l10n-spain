# Copyright 2025 Factor Libre - Almudena de La Puente
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _process_vat_book_tax_fee_info(self, res, tax, sign):
        return self._process_aeat_tax_fee_info(res, tax, sign)
