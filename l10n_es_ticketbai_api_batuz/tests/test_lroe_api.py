# Copyright (2021) Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json
from requests import exceptions
from datetime import datetime
from odoo.tests import common
from ..lroe.lroe_api import LROETicketBaiApi


@common.at_install(False)
@common.post_install(True)
class TestLroeTicketBaiApi(common.TransactionCase):

    def test_get_request_headers(self):
        api = LROETicketBaiApi(None)

        class Company:
            vat = 'VAT'
            name = 'Name'
            partner_id = self.env.ref("l10n_es_ticketbai_api.res_partner_binovo")

        class Op:
            tbai_invoice_ids = False
            company_id = Company()
            model = 'MODE'

            def build_cabecera_ejercicio(self):
                return str(datetime.now().year)

        h = api.get_request_headers(Op())

        data = json.loads(h['eus-bizkaia-n3-data'])
        self.assertEqual('B20990602', data["inte"]['nif'])  # Sin el código país
        self.assertEqual('Name', data['inte']['nrs'])
        self.assertEqual('MODE', data['drs']['mode'])

    def test_without_cert_raises(self):
        api = LROETicketBaiApi(None)
        with self.assertRaises(exceptions.RequestException):
            api.post(None, None)

    def test_requests_post(self):
        api = LROETicketBaiApi(None)

        class C:
            pass

        def post_200(*args, **kwargs):
            r = C()
            r.headers = 'headers'
            r.raise_for_status = lambda: None
            r.content = 'data'
            r.status_code = 200
            r.reason = 'reason'
            return r
        api.post = post_200
        r = api.requests_post(None, None)
        self.assertEqual(False, r.error)
        self.assertEqual('data', r.data)
        self.assertEqual('headers', r.headers)

        def post_400(*args, **kwargs):
            r = C()
            r.headers = 'headers'
            r.raise_for_status = lambda: None
            r.content = 'data'
            r.status_code = 400
            r.reason = 'reason'
            return r
        api.post = post_400
        r = api.requests_post(None, None)
        self.assertEqual(True, r.error)

        def post_raise_response(*args, **kwargs):

            def do_raise():
                e = exceptions.RequestException()
                e.response = C()
                e.response.status_code = 401
                e.response.text = '{"message": "msg"}'
                raise e
            r = C()
            r.headers = 'headers'
            r.raise_for_status = do_raise
            r.content = 'data'
            r.status_code = 400
            r.reason = 'reason'
            return r
        api.post = post_raise_response
        r = api.requests_post(None, None)
        self.assertEqual(True, r.error)
        self.assertEqual(401, r.errno)

        def post_raise_no_response(*args, **kwargs):

            def do_raise():
                e = exceptions.RequestException()
                e.errno = 402
                raise e
            r = C()
            r.headers = 'headers'
            r.raise_for_status = do_raise
            r.content = 'data'
            r.status_code = 400
            r.reason = 'reason'
            return r
        api.post = post_raise_no_response
        r = api.requests_post(None, None)
        self.assertEqual(True, r.error)
        self.assertEqual(402, r.errno)
