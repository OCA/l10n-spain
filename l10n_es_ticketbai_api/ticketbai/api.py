# Copyright 2021 Binovo IT Human Project SL
# Copyright 2021 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import requests
from requests import exceptions

from odoo.tools.safe_eval import safe_eval


class TicketBaiResponse:
    __slots__ = ["data", "error", "strerror", "errno"]

    def __init__(self, data=None, error=False, strerror="", errno=0):
        self.data = data
        self.error = error
        self.strerror = strerror
        self.errno = errno


class TicketBaiApi:
    __slots__ = ["url", "p12_buffer", "password", "cert", "key"]

    def __init__(self, url, **kwargs):
        self.url = url
        self.p12_buffer = kwargs.get("p12_buffer", None)
        self.password = kwargs.get("password", None)
        self.cert = kwargs.get("cert", None)
        self.key = kwargs.get("key", None)

    def post(self, data):
        headers = {"Content-Type": "application/xml; charset=UTF-8"}
        if self.cert and self.key:
            response = requests.post(
                url=self.url,
                data=data,
                headers=headers,
                cert=(self.cert, self.key),
                timeout=20,
            )
        else:
            raise exceptions.RequestException(
                errno="1",
                strerror="Please provide cert and key.",
            )
        return response

    def requests_post(self, data):
        try:
            response = self.post(data)
            data = response.content.decode(response.encoding)
            if 200 == response.status_code:
                tb_response = TicketBaiResponse(data=data)
            else:
                tb_response = TicketBaiResponse(
                    error=True, strerror=response.reason, errno=response.status_code
                )
        except exceptions.RequestException as re:
            if hasattr(re, "response") and re.response:
                errno = re.response.status_code
                content = safe_eval(re.response.text)
                strerror = content["message"]
            else:
                errno = re.errno
                strerror = re.strerror
            tb_response = TicketBaiResponse(error=True, strerror=strerror, errno=errno)
        return tb_response
