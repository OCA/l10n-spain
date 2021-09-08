# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging
from requests import exceptions
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)

try:
    from requests_pkcs12 import post as pkcs12_post
except(ImportError, IOError) as err:
    _logger.error(err)


class TicketBaiResponse:

    def __init__(self, data=None, error=False, strerror='', errno=0):
        self.data = data
        self.error = error
        self.strerror = strerror
        self.errno = errno


class TicketBaiApi:

    def __init__(self, url, **kwargs):
        self.url = url
        self.p12_buffer = kwargs.get('p12_buffer', None)
        self.password = kwargs.get('password', None)
        self.cert = kwargs.get('cert', None)
        self.key = kwargs.get('key', None)

    def post(self, data):
        headers = {
            'Content-Type': 'application/xml; charset=UTF-8'
        }
        if self.cert is None and self.key is None:
            response = pkcs12_post(
                self.url, data=data, headers=headers, pkcs12_data=self.p12_buffer,
                pkcs12_password=self.password)
        elif self.p12_buffer is None and self.password is None:
            response = pkcs12_post(
                self.url, data=data, headers=headers, cert=(self.cert, self.key))
        else:
            raise exceptions.RequestException(
                errno='1',
                strerror='Please provide cert and key, or p12 buffer and its password.')
        return response

    def requests_post(self, data):
        try:
            response = self.post(data)
            data = response.content.decode(response.encoding)
            if 200 == response.status_code:
                tb_response = TicketBaiResponse(data=data)
            else:
                tb_response = TicketBaiResponse(
                    error=True, strerror=response.reason, errno=response.status_code)
        except exceptions.RequestException as re:
            if hasattr(re, 'response') and re.response:
                errno = re.response.status_code
                content = safe_eval(re.response.text)
                strerror = content['message']
            else:
                errno = re.errno
                strerror = re.strerror
            tb_response = TicketBaiResponse(error=True, strerror=strerror, errno=errno)
        return tb_response
