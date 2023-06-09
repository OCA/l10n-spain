# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models

from .confirming_aef import ConfirmingAEF


class AccountPaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def generate_payment_file(self):
        self.ensure_one()
        if self.payment_method_id.code == "confirming_aef":
            # AEF payment file
            return ConfirmingAEF(self).create_file()
        return super().generate_payment_file()
