# Copyright 2024 Worldwide Vision Business Solutions SL - Gil Arasa Verge
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["conf_sabadell"] = {"mode": "multi", "domain": [("type", "=", "bank")]}
        return res
