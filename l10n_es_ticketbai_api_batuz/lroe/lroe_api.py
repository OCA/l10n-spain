# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
import logging

from requests import exceptions

from odoo.tools.safe_eval import safe_eval

from odoo.addons.l10n_es_ticketbai_api.ticketbai.api import TicketBaiApi

_logger = logging.Logger(__name__)

try:
    from requests_pkcs12 import post as pkcs12_post
except (ImportError, IOError) as err:
    _logger.info(err)


class LROEOperationResponse:
    def __init__(self, data=None, headers=None, error=False, strerror="", errno=0):
        self.data = data
        self.headers = headers
        self.error = error
        self.strerror = strerror
        self.errno = errno

    def get_lroe_srv_response_type(self):
        headers = self.headers
        return headers and headers.get("eus-bizkaia-n3-tipo-respuesta") or None

    def get_lroe_srv_response_code(self):
        headers = self.headers
        return headers and headers.get("eus-bizkaia-n3-codigo-respuesta") or None

    def get_lroe_srv_response_message(self):
        headers = self.headers
        return headers and headers.get("eus-bizkaia-n3-mensaje-respuesta") or None

    def get_lroe_srv_response_record_id(self):
        headers = self.headers
        return headers and headers.get("eus-bizkaia-n3-identificativo") or None

    def get_lroe_srv_response_record_number(self):
        headers = self.headers
        return headers and headers.get("eus-bizkaia-n3-numero-registro") or None

    def get_lroe_srv_response_record_date(self):
        headers = self.headers
        return headers and headers.get("date") or None


class LROETicketBaiApi(TicketBaiApi):
    @staticmethod
    def get_request_headers(lroe_operation):
        def set_default_headers(headers):
            headers["Accept-Encoding"] = "gzip"
            headers["Content-Encoding"] = "gzip"
            headers["Content-Length"] = 0
            headers["Content-Type"] = "application/octet-stream"

        def set_eus_bizkaia_n3_headers(headers):
            def set_eus_bizkaia_n3_data():

                if hasattr(lroe_operation, "lroe_chapter_id"):
                    apa = (
                        lroe_operation.lroe_subchapter_id.code
                        or lroe_operation.lroe_chapter_id.code
                    )
                else:
                    apa = "1.1"
                partner = lroe_operation.company_id.partner_id
                nif = partner.tbai_get_value_nif()
                n3_dat_dict = {
                    "con": "LROE",
                    "apa": apa,
                    "inte": {"nif": nif, "nrs": lroe_operation.company_id.name},
                    "drs": {
                        "mode": lroe_operation.model,
                        "ejer": lroe_operation.build_cabecera_ejercicio(),
                    },
                }
                return json.dumps(n3_dat_dict)

            headers["eus-bizkaia-n3-version"] = "1.0"
            headers["eus-bizkaia-n3-content-type"] = "application/xml"
            headers["eus-bizkaia-n3-data"] = set_eus_bizkaia_n3_data()

        headers = {}
        set_default_headers(headers)
        set_eus_bizkaia_n3_headers(headers)
        return headers

    def post(self, request_headers, data):
        if self.cert is None and self.key is None:
            response = pkcs12_post(
                self.url,
                data=data,
                headers=request_headers,
                pkcs12_data=self.p12_buffer,
                pkcs12_password=self.password,
            )
        elif self.p12_buffer is None and self.password is None:
            response = pkcs12_post(
                self.url, data=data, headers=request_headers, cert=(self.cert, self.key)
            )
        else:
            raise exceptions.RequestException(
                1, "Please provide cert and key, or p12 buffer and its password."
            )
        return response

    def requests_post(self, request_headers, data):
        response_headers = {}
        try:
            response = self.post(request_headers, data)
            response_headers = response.headers
            response.raise_for_status()
            response_data = response.content
            if 200 == response.status_code:
                lroe_response = LROEOperationResponse(
                    data=response_data, headers=response_headers
                )
            else:
                lroe_response = LROEOperationResponse(
                    error=True,
                    headers=response_headers,
                    strerror=response.reason,
                    errno=response.status_code,
                )
        except exceptions.RequestException as re:
            if hasattr(re, "response") and re.response:
                errno = re.response.status_code
                content = safe_eval(re.response.text)
                strerror = content["message"]
            else:
                errno = re.errno
                strerror = re.strerror
            lroe_response = LROEOperationResponse(
                error=True, headers=response_headers, strerror=strerror, errno=errno
            )
        return lroe_response
