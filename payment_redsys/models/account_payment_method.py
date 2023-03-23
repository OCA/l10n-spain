# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["redsys"] = {"mode": "multi", "domain": [("type", "=", "bank")]}
        return res
