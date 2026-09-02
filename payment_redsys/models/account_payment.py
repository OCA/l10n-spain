# Copyright 2025 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
import json

import requests

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class AccountPayment(models.Model):
    _inherit = "account.payment"

    redsys_auth_amount = fields.Float(
        "Redsys Authorized Amount",
        compute="_compute_redsys_auth_amount",
        store=True,
        readonly=False,
    )
    redsys_auth_done = fields.Boolean("Redsys Authorized Done", default=False)
    redsys_auth_txnid = fields.Char("Redsys Auth Transaction ID")
    is_redsys_auth = fields.Boolean(
        "Is Redsys Authorized",
        compute="_compute_is_redsys_auth",
        store=True,
        help="Indicates if this payment is a Redsys authorization.",
    )

    @api.depends("payment_transaction_id.provider_id.redsys_transaction_type")
    def _compute_is_redsys_auth(self):
        for payment in self:
            provider = payment.payment_transaction_id.provider_id
            payment.is_redsys_auth = provider.redsys_transaction_type == "1"

    @api.depends("amount")
    def _compute_redsys_auth_amount(self):
        for order in self:
            order.redsys_auth_amount = order.amount

    def _get_redsys_rest_urls(self, environment):
        """Redsys Rest URLs"""
        params = self.env["ir.config_parameter"].sudo()
        if environment == "prod":
            return params.get_param("payment_redsys.url_authorize_prod")
        else:
            return params.get_param("payment_redsys.url_authorize_test")

    def redsys_authorize_amount(self):
        self.ensure_one()
        transaction = self.payment_transaction_id
        provider = transaction.provider_id
        if provider.redsys_transaction_type != "1":
            raise ValidationError(
                _(
                    "Redsys: Transaction type must be '1' for preauthorization, "
                    "current value is '%s'."
                )
                % provider.redsys_transaction_type
            )
        if self.redsys_auth_amount == 0.0:
            raise ValidationError(
                _("Redsys: Authorization amount must be set before authorizing.")
            )
        if self.redsys_auth_done:
            raise ValidationError(
                _("Redsys: Authorization already done for this transaction.")
            )
        merchant_parameters = {
            "Ds_Merchant_Amount": str(int(round(self.redsys_auth_amount, 2) * 100)),
            "Ds_Merchant_Currency": provider.redsys_currency or "978",
            "Ds_Merchant_MerchantCode": (
                provider.redsys_merchant_code and provider.redsys_merchant_code[:9]
            ),
            "Ds_Merchant_Order": transaction.reference,
            "Ds_Merchant_Terminal": provider.redsys_terminal or "1",
            "Ds_Merchant_TransactionType": "2",
        }
        merchant_parameters64 = provider._url_encode64(json.dumps(merchant_parameters))
        redsys_values = {
            "Ds_SignatureVersion": str(provider.redsys_signature_version),
            "Ds_MerchantParameters": merchant_parameters64,
            "Ds_Signature": provider.sign_parameters(
                provider.redsys_secret_key, merchant_parameters64
            ),
        }
        environment = "prod" if provider.state == "enabled" else "test"
        url = self._get_redsys_rest_urls(environment)
        response = requests.post(url, data=redsys_values, timeout=60)
        if "Ds_MerchantParameters" in response.json():
            parameters = response.json().get("Ds_MerchantParameters", "")
            parameters_dic = json.loads(base64.b64decode(parameters).decode())
            if (
                "Ds_AuthorisationCode" in parameters_dic
                and "Ds_Response" in parameters_dic
            ):
                if parameters_dic.get("Ds_Response") == "0900":
                    self.redsys_auth_txnid = parameters_dic.get("Ds_AuthorisationCode")
                    self.redsys_auth_done = True
                    post_message = _("Redsys Auth done: %s") % (
                        parameters_dic.get("Ds_AuthorisationCode")
                    )
                    self.message_post(body=post_message)
                    if self.state != "draft":
                        self.action_draft()
                    self.amount = self.redsys_auth_amount
                    self.action_post()
                else:
                    post_message = _("Error Redsys Auth: %s") % (str(parameters_dic))
                    self.message_post(body=post_message)
            else:
                post_message = _("Error Redsys Auth: %s") % (str(parameters_dic))
                self.message_post(body=post_message)
        else:
            post_message = _("Error Redsys Auth: %s") % (str(response.json()))
            self.message_post(body=post_message)
