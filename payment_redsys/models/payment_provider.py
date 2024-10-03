# Copyright 2016-2017 Tecnativa - Sergio Teruel
# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2020 Tecnativa - João Marques
# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64
import hashlib
import hmac
import json
import logging
import urllib

from Crypto.Cipher import DES3  # pylint: disable=W7936 - No real warning
from werkzeug import urls

from odoo import api, fields, http, models
from odoo.tools import config

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    def _redsys_get_api_url(self):
        if self.state == "enabled":
            return "https://sis.redsys.es/sis/realizarPago/"
        else:  # test environment
            return "https://sis-t.redsys.es:25443/sis/realizarPago/"

    code = fields.Selection(
        selection_add=[("redsys", "Redsys")], ondelete={"redsys": "set default"}
    )
    redsys_merchant_name = fields.Char("Merchant Name", required_if_provider="redsys")
    redsys_merchant_code = fields.Char("Merchant code", required_if_provider="redsys")
    redsys_merchant_description = fields.Char(
        "Product Description", required_if_provider="redsys"
    )
    redsys_secret_key = fields.Char("Secret Key", required_if_provider="redsys")
    redsys_terminal = fields.Char(
        "Terminal", default="1", required_if_provider="redsys"
    )
    redsys_currency = fields.Char(
        "Currency", default="978", required_if_provider="redsys"
    )
    redsys_transaction_type = fields.Char(
        "Transtaction Type", default="0", required_if_provider="redsys"
    )
    redsys_merchant_data = fields.Char("Merchant Data")
    redsys_merchant_lang = fields.Selection(
        [
            ("001", "Castellano"),
            ("002", "Inglés"),
            ("003", "Catalán"),
            ("004", "Francés"),
            ("005", "Alemán"),
            ("006", "Holandés"),
            ("007", "Italiano"),
            ("008", "Sueco"),
            ("009", "Portugués"),
            ("010", "Valenciano"),
            ("011", "Polaco"),
            ("012", "Gallego"),
            ("013", "Euskera"),
        ],
        "Merchant Consumer Language",
        default="001",
    )
    redsys_pay_method = fields.Selection(
        [
            ("T", "Pago con Tarjeta"),
            ("R", "Pago por Transferencia"),
            ("D", "Domiciliacion"),
            ("z", "Bizum"),
        ],
        "Payment Method",
        default="T",
    )
    redsys_signature_version = fields.Selection(
        [("HMAC_SHA256_V1", "HMAC SHA256 V1")], default="HMAC_SHA256_V1"
    )

    @api.model
    def _get_website_callback_url(self):
        """For force a callback url from Redsys distinct to base url website,
        only apply to a Redsys response.
        """
        get_param = self.env["ir.config_parameter"].sudo().get_param
        return get_param("payment_redsys.callback_url")

    @api.model
    def _get_website_url(self):
        """
        For a single website setting the domain website name is not accesible
        for the user, by default is localhost so the system get domain from
        system parameters instead of domain of website record.
        """
        if config["test_enable"]:
            return self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        # For a JSON request, there's no `website` attribute. Fallback to context if any
        website = (
            hasattr(http.request, "website")
            and http.request.website
            or self.env.context.get("website_id")
            and self.env["website"].browse(self.env.context["website_id"])
        )
        domain = website and website.domain
        if domain and domain != "localhost":
            # Check domain scheme as Odoo does in `website._get_http_domain()`
            parsed_url = urls.url_parse(domain)
            base_url = (
                "{}://{}".format(
                    http.request.httprequest.environ["wsgi.url_scheme"], domain
                )
                if not parsed_url.scheme
                else domain
            )
        else:
            base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        return base_url or ""

    def _prepare_merchant_parameters(self, tx_values):
        # Check multi-website
        base_url = self._get_website_url()
        callback_url = self._get_website_callback_url()
        values = {
            "Ds_Sermepa_Url": self.redsys_get_form_action_url(),
            "Ds_Merchant_Amount": str(int(round(tx_values["amount"] * 100))),
            "Ds_Merchant_Currency": self.redsys_currency or "978",
            "Ds_Merchant_Order": (
                tx_values["reference"] and tx_values["reference"][-12:] or False
            ),
            "Ds_Merchant_MerchantCode": (
                self.redsys_merchant_code and self.redsys_merchant_code[:9]
            ),
            "Ds_Merchant_Terminal": self.redsys_terminal or "1",
            "Ds_Merchant_TransactionType": (self.redsys_transaction_type or "0"),
            "Ds_Merchant_Titular": tx_values.get(
                "billing_partner", self.env.user.partner_id
            ).display_name[:60],
            "Ds_Merchant_MerchantName": (
                self.redsys_merchant_name and self.redsys_merchant_name[:25]
            ),
            "Ds_Merchant_MerchantUrl": (
                "%s/payment/redsys/return" % (callback_url or base_url)
            )[:250],
            "Ds_Merchant_MerchantData": self.redsys_merchant_data or "",
            "Ds_Merchant_ProductDescription": (
                self._product_description(tx_values["reference"])
                or self.redsys_merchant_description
                and self.redsys_merchant_description[:125]
            ),
            "Ds_Merchant_ConsumerLanguage": (self.redsys_merchant_lang or "001"),
            "Ds_Merchant_UrlOk": "%s/payment/redsys/result/redsys_result_ok" % base_url,
            "Ds_Merchant_UrlKo": "%s/payment/redsys/result/redsys_result_ko" % base_url,
            "Ds_Merchant_Paymethods": self.redsys_pay_method or "T",
        }
        return self._url_encode64(json.dumps(values)).decode("utf-8")

    def _url_encode64(self, data):
        data = base64.b64encode(data.encode())
        return data

    def _url_decode64(self, data):
        return json.loads(base64.b64decode(data).decode())

    def sign_parameters(self, secret_key, params64):
        params_dic = self._url_decode64(params64)
        if "Ds_Merchant_Order" in params_dic:
            order = str(params_dic["Ds_Merchant_Order"])
        else:
            order = str(urllib.parse.unquote(params_dic.get("Ds_Order", "Not found")))
        cipher = DES3.new(
            key=base64.b64decode(secret_key), mode=DES3.MODE_CBC, IV=b"\0\0\0\0\0\0\0\0"
        )
        diff_block = len(order) % 8
        zeros = diff_block and (b"\0" * (8 - diff_block)) or b""
        key = cipher.encrypt(str.encode(order + zeros.decode()))
        if isinstance(params64, str):
            params64 = params64.encode()
        dig = hmac.new(key=key, msg=params64, digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    def redsys_get_form_action_url(self):
        self.ensure_one()
        return self._redsys_get_api_url()

    def _product_description(self, order_ref):
        sale_order = self.env["sale.order"].search([("name", "=", order_ref)])
        res = ""
        if sale_order:
            description = "|".join(x.name for x in sale_order.order_line)
            res = description[:125]
        return res

    def _get_default_payment_method_id(self, code):
        self.ensure_one()
        if self.code != "redsys":
            return super()._get_default_payment_method_id(code)
        return self.env.ref("payment_redsys.payment_method_redsys").id
