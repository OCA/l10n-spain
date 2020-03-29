# Copyright 2020 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
import requests
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class TicketBaiResponse:

    def __init__(self, data=None, error=False, strerror='', errno=0):
        self.data = data
        self.error = error
        self.strerror = strerror
        self.errno = errno


class TicketBaiApi:

    def __init__(self, url, public_key, private_key):
        self.url = url
        self.cert = public_key
        self.key = private_key

    def requests_post(self, data):
        headers = {
            'Content-Type': 'application/xml; charset=UTF-8'
        }
        try:
            response = requests.post(
                self.url, data=data, headers=headers, cert=(self.cert, self.key))
            response.raise_for_status()
            data = response.content.decode(response.encoding)
            _logger.debug(data)
            if 200 == response.status_code:
                tb_response = TicketBaiResponse(data=data)
            else:
                tb_response = TicketBaiResponse(
                    error=True, strerror=response.reason, errno=response.status_code)
        except requests.exceptions.RequestException as re:
            _logger.debug(re)
            if hasattr(re, 'response'):
                errno = re.response.status_code
                content = safe_eval(re.response.text)
                strerror = content['message']
            else:
                errno = re.errno
                strerror = re.strerror
            tb_response = TicketBaiResponse(error=True, strerror=strerror, errno=errno)
        return tb_response
