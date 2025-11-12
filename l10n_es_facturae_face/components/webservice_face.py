# Copyright 2020 Creu Blanca
# @author: Enric Tobella
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import hashlib
from datetime import datetime, timedelta

import jwt
import requests
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization

from odoo.exceptions import UserError

from odoo.addons.component.core import Component


class WebServiceFace(Component):
    _name = "base.webservice.face"
    _usage = "face.protocol"
    _backend_type = "l10n_es_facturae"
    _inherit = "edi.component.mixin"
    _request_timeout = 30

    def generate_jwt(self, public_cert, private_key):
        with open(public_cert, "rb") as f:
            certificate = x509.load_pem_x509_certificate(
                f.read(), backend=default_backend()
            )
        with open(private_key, "rb") as f:
            key = f.read()
        username = base64.b64encode(
            certificate.public_bytes(serialization.Encoding.DER)
        ).decode("utf-8")
        headers = {
            "alg": "RS256",
            "typ": "JWT",
            "x5c": [username],
        }
        return jwt.encode(
            {
                "iat": int(datetime.now().timestamp()),
                "exp": int((datetime.now() + timedelta(minutes=5)).timestamp()),
                "username": hashlib.sha1(username.encode("utf-8")).hexdigest(),
            },
            key,
            algorithm="RS256",
            headers=headers,
        )

    def send_webservice(
        self, public_crt, private_key, file_data, file_name, email, anexos_list=False
    ):
        jwt_token = self.generate_jwt(public_crt, private_key)
        server = (
            self.env["ir.config_parameter"].sudo().get_param("facturae.face.ws_rest")
        )
        response = requests.post(
            f"{server}/providers/v1/invoices",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "User-Agent": "",
            },
            json={
                "filename": file_name,
                "content": base64.b64encode(file_data.encode("utf-8")).decode("utf-8"),
                "email": email,
                "attachments": [
                    {
                        "filename": anexo.file_name,
                        "content": anexo.file_data,
                    }
                    for anexo in anexos_list
                ]
                if anexos_list
                else [],
            },
            timeout=self._request_timeout,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UserError(f"Error Sending invoice: {e}") from e
        return response.json()

    def consult_invoice(self, public_crt, private_key, invoice_number):
        jwt_token = self.generate_jwt(public_crt, private_key)
        server = (
            self.env["ir.config_parameter"].sudo().get_param("facturae.face.ws_rest")
        )
        response = requests.get(
            f"{server}/providers/v1/invoices/{invoice_number}",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "User-Agent": "",
            },
            timeout=self._request_timeout,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UserError(f"Error consulting invoice: {e}") from e
        return response.json()

    def cancel(self, public_crt, private_key, identifier, motive):
        jwt_token = self.generate_jwt(public_crt, private_key)
        server = (
            self.env["ir.config_parameter"].sudo().get_param("facturae.face.ws_rest")
        )
        response = requests.post(
            f"{server}/providers/v1/invoices/{identifier}/cancellation-requests",
            headers={
                "Authorization": f"Bearer {jwt_token}",
                "Content-Type": "application/json",
                "User-Agent": "",
            },
            json={
                "comment": motive,
            },
            timeout=self._request_timeout,
        )
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            raise UserError(f"Error canceling invoice: {e}") from e
        return response.json()
