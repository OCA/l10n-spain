# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models
from odoo.tools.bank_account_number import get_iban_part


class ResPartnerBank(models.Model):
    _inherit = "res.partner.bank"

    def _get_facturae_bank_code(self):
        """National bank code of the IBAN, the code of the bank (res.bank)
        that base_bank_from_iban filled from the IBAN up to 19.0."""
        self.ensure_one()
        if self.account_type != "iban":
            return False
        return get_iban_part(self.account_number, "bank") or False
