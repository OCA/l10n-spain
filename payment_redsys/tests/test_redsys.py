# -*- coding: utf-8 -*-
# © 2016-2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

import urllib
from lxml import objectify
import json
from mock import ANY, patch

from openerp import http
from openerp.tests.common import HttpCase

_logger = logging.getLogger(__name__)


class RedsysCase(HttpCase):
    def setUp(self):
        super(RedsysCase, self).setUp()
        with self.cursor() as cr:
            env = self.env(cr)
            self.currency_euro = env['res.currency'].search([
                ('name', '=', 'EUR')
            ], limit=1)
            self.country_spain = env['res.country'].search([
                ('code', '=', 'ES')
            ], limit=1)
            self.buyer_values = {
                'partner_name': 'Norbert Buyer',
                'partner_lang': 'en_US',
                'partner_email': 'norbert.buyer@example.com',
                'partner_address': 'Huge Street 2/543',
                'partner_phone': '0032 12 34 56 78',
                'partner_city': 'Sin City',
                'partner_zip': '1000',
                'partner_country': self.country_spain.id,
                'partner_country_id': self.country_spain.id,
                'partner_country_name': 'Belgium',
                'billing_partner_name': 'Norbert Buyer',
                'billing_partner_lang': 'en_US',
                'billing_partner_email': 'norbert.buyer@example.com',
                'billing_partner_address': 'Huge Street 2/543',
                'billing_partner_phone': '0032 12 34 56 78',
                'billing_partner_city': 'Sin City',
                'billing_partner_zip': '1000',
                'billing_partner_country': self.country_spain.id,
                'billing_partner_country_id': self.country_spain.id,
                'billing_partner_country_name': 'Belgium',
            }

            # test partner
            self.buyer = env['res.partner'].create({
                'name': 'Norbert Buyer',
                'lang': 'en_US',
                'email': 'norbert.buyer@example.com',
                'street': 'Huge Street',
                'street2': '2/543',
                'phone': '0032 12 34 56 78',
                'city': 'Sin City',
                'zip': '1000',
                'country_id': self.country_spain.id
            })
            self.buyer_id = self.buyer.id
            self.redsys = env.ref('payment_redsys.payment_acquirer_redsys')
            self.redsys.redsys_merchant_code = '069611024'
            self.redsys.redsys_secret_key = 'sq7HjrUOBfKmC576ILgskD5srU870gJ8'
            self.redsys.send_quotation = False
            self.redsys_ds_parameters = {
                'Ds_AuthorisationCode': '999999',
                'Ds_Date': '14%2F05%2F2017',
                'Ds_Card_Brand': '1',
                'Ds_SecurePayment': '1',
                'Ds_MerchantData': 'xxx',
                'Ds_Card_Country': '724',
                'Ds_Terminal': '001',
                'Ds_MerchantCode': '069611024',
                'Ds_ConsumerLanguage': '1',
                'Ds_Response': '0000',
                'Ds_Order': 'TST0001',
                'Ds_Currency': '978',
                'Ds_Amount': '10050',
                'Ds_TransactionType': '0',
                'Ds_Hour': '08%3A29',
            }
            self.vals_tx = {
                'amount': 100.50,
                'acquirer_id': self.redsys.id,
                'currency_id': self.currency_euro.id,
                'reference': 'TST0001',
                'partner_id': self.buyer_id,
            }
            self.tx = env['payment.transaction'].create(self.vals_tx)
            self.partner = env['res.partner'].create({
                'name': 'Partner Test',
            })
            self.product = env['product.product'].create({
                'name': 'Test Product',
                'list_price': 100.50,
            })
            self.so = env['sale.order'].create({
                'partner_id': self.partner.id,
                'partner_invoice_id': self.partner.id,
                'partner_shipping_id': self.partner.id,
                'order_line': [
                    (0, 0, {
                        'name': 'Test',
                        'product_id': self.product.id,
                        'product_uom_qty': 1,
                        'product_uom': self.product.uom_id.id,
                        'price_unit': self.product.list_price,
                        'tax_id': [(6, 0, [])],
                    })],
                'pricelist_id': env.ref('product.list0').id,
            })
            merchant_parameters = self.redsys._prepare_merchant_parameters(
                self.redsys, self.vals_tx)
            self.ds_signature = self.redsys.sign_parameters(
                self.redsys.redsys_secret_key, merchant_parameters)

    def data_post_redsys(self, url=None, data=None, timeout=10):
        data_encode = None
        if data:
            data_encode = urllib.urlencode(data)
        doc = self.url_open(url, data=data_encode, timeout=timeout)
        return doc

    def test_10_redsys_form_render(self):
        # be sure not to do stupid things
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')

        # ----------------------------------------
        # Test: button direct rendering
        # ----------------------------------------

        # render the button
        res = self.redsys.render(
            'TST0001', 100.50, self.currency_euro.id,
            partner_id=None,
            values=self.buyer_values)

        # check form result
        tree = objectify.fromstring(res[0])
        self.assertEqual(
            tree.get('action'),
            'https://sis-t.redsys.es:25443/sis/realizarPago/',
            'Redsys: wrong form POST url')

        for form_input in tree.input:
            if form_input.get('name') in ['submit']:
                continue
            if form_input.get('name') == 'Ds_MerchantParameters':
                DS_parameters = self.redsys._url_decode64(
                    form_input.get('value'))
                self.assertEqual(DS_parameters['Ds_Merchant_Order'], 'TST0001')
                self.assertEqual(
                    DS_parameters['Ds_Merchant_MerchantUrl'],
                    '%s/payment/redsys/return' % base_url)
        # Form values
        values = self.redsys.redsys_form_generate_values(
            self.redsys.id, self.vals_tx)
        self.assertEqual(
            values['Ds_Signature'],
            self.ds_signature,
            'Redsys: Sign failed')

    def test_20_redsys_form_management(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(redsys.environment,
                             'test', 'test without test environment')
            DS_parameters = redsys._url_encode64(
                json.dumps(self.redsys_ds_parameters))
            # typical data posted by redsys after client has successfully paid
            redsys_post_data = {
                'Ds_Signature': '5PmN2yITrEFS/TkdL1d27DOWgaIE/AaB/NPu6AwtjHM=',
                'Ds_MerchantParameters': DS_parameters,
                'Ds_SignatureVersion': u'HMAC_SHA256_V1',
            }
        self.data_post_redsys(url='/payment/redsys/return',
                              data=redsys_post_data)
        with self.cursor() as cr:
            env = self.env(cr)
            tx = self.tx.with_env(env)
            self.assertEqual(tx.redsys_txnid, '999999',
                             'Redsys: Get transaction')
            self.assertEqual(tx.reference, 'TST0001',
                             'Redsys: Get transaction')
            # check state
            self.assertEqual(
                tx.state, 'done',
                'Redsys: validation did not put tx into done state')
            self.assertEqual(
                tx.redsys_txnid,
                self.redsys_ds_parameters.get('Ds_AuthorisationCode'),
                'Redsys: validation did not update tx payid')

    def test_30_redsys_form_management(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(redsys.environment, 'test',
                             'test without test environment')
            unknow_tx = self.redsys_ds_parameters.copy()
            unknow_tx['Ds_Order'] = '22'
            DS_parameters = redsys._url_encode64(json.dumps(unknow_tx))
            # typical data posted by redsys after client has successfully paid
            redsys_post_data = {
                'Ds_Signature': '5PmN2yITrEFS/TkdL1d27DOWgaIE/AaB/NPu6AwtjHM=',
                'Ds_MerchantParameters': DS_parameters,
                'Ds_SignatureVersion': u'HMAC_SHA256_V1',
            }
        self.session.test_enable = True
        http.root.session_store.save(self.session)
        self.data_post_redsys(
            url='/payment/redsys/return', data=redsys_post_data)
        self.assertEqual(
            http.OpenERPSession.tx_error, True,
            'test with unknow transacction'
        )

    def test_40_redsys_form_error(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(redsys.environment, 'test',
                             'test without test environment')
            # Force error from provider
            error_tx = self.redsys_ds_parameters.copy()
            error_tx['Ds_Response'] = '9065'
            DS_parameters = redsys._url_encode64(json.dumps(error_tx))
            # typical data posted by redsys after client has successfully paid
            redsys_post_data = {
                'Ds_Signature': 'h7R4n9cQeASVkjWnTkCkRq8K2N10B7iZGDzza5dc2Xk=',
                'Ds_MerchantParameters': DS_parameters,
                'Ds_SignatureVersion': u'HMAC_SHA256_V1',
            }
        self.data_post_redsys(
            url='/payment/redsys/return', data=redsys_post_data)
        with self.cursor() as cr:
            env = self.env(cr)
            tx = self.tx.with_env(env)
            # Get transaction
            self.assertNotEqual(
                tx.state, 'done',
                'Redsys: validation did not put tx into done state')

    def test_50_redsys_form_pending(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(redsys.environment, 'test',
                             'test without test environment')
            # Force error from provider
            error_tx = self.redsys_ds_parameters.copy()
            error_tx['Ds_Response'] = '110'
            DS_parameters = redsys._url_encode64(json.dumps(error_tx))
            # typical data posted by redsys after client has successfully paid
            redsys_post_data = {
                'Ds_Signature': '2pSk3Z5XzLM1H/Mcrphzj3mtEDEcC7exrg3Fv+rVY10=',
                'Ds_MerchantParameters': DS_parameters,
                'Ds_SignatureVersion': u'HMAC_SHA256_V1',
            }
        self.data_post_redsys(url='/payment/redsys/return',
                              data=redsys_post_data)
        with self.cursor() as cr:
            env = self.env(cr)
            tx = self.tx.with_env(env)
            # Get transaction
            self.assertEqual(
                tx.state, 'pending',
                'Redsys: validation did not put tx into done state')

    def test_60_redsys_form_cancel(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(
                redsys.environment, 'test', 'test without test environment')
            # Force error from provider
            error_tx = self.redsys_ds_parameters.copy()
            error_tx['Ds_Response'] = '912'
            DS_parameters = redsys._url_encode64(json.dumps(error_tx))
            # typical data posted by redsys after client has successfully paid
            redsys_post_data = {
                'Ds_Signature': 'q2YGZwpRi0tiT86L/DDypjIN6HeGTbiUqBPPYOMfxr8=',
                'Ds_MerchantParameters': DS_parameters,
                'Ds_SignatureVersion': u'HMAC_SHA256_V1',
            }
        self.data_post_redsys(url='/payment/redsys/return',
                              data=redsys_post_data)
        with self.cursor() as cr:
            env = self.env(cr)
            tx = self.tx.with_env(env)
            # Get transaction
            self.assertEqual(
                tx.state, 'cancel',
                'Redsys: validation did not put tx into done state')

    def test_80_redsys_partial_payment(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(
                self.redsys.environment, 'test',
                'test without test environment')
            redsys.redsys_percent_partial = 50
            # Form values
            values = redsys.redsys_form_generate_values(
                redsys.id, self.vals_tx)
            Ds_MerchantParameters = self.redsys._url_decode64(
                values['Ds_MerchantParameters'])
            self.assertEqual(
                Ds_MerchantParameters['Ds_Merchant_Amount'], '5025',
                'Redsys: Partial amount Ok')

    @patch('openerp.addons.sale.sale.SaleOrder.action_confirm')
    @patch('openerp.addons.sale.sale.SaleOrder.force_quotation_send')
    def test_90_redsys_form_partial_payment(self, mock_quo_send, mock_confirm):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            tx = self.tx.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(
                redsys.environment, 'test', 'test without test environment')
            redsys.redsys_percent_partial = 50
            params = self.redsys_ds_parameters.copy()
            params['Ds_Amount'] = '5025'
            DS_parameters = redsys._url_encode64(json.dumps(params))
            # typical data posted by redsys after client has successfully paid
            redsys_post_data = {
                'Ds_Signature': 'Glo50HlVTtkshKvr/eEYfQUggegbsoqHGw/AflqxN9M=',
                'Ds_MerchantParameters': DS_parameters,
                'Ds_SignatureVersion': u'HMAC_SHA256_V1',
            }
            tx.sale_order_id = self.so.with_env(env).id
            # Get transaction
        self.data_post_redsys(
            url='/payment/redsys/return', data=redsys_post_data)
        with self.cursor() as cr:
            mock_confirm.assert_called_once_with(
                cr, self.env.uid, tx.sale_order_id.ids, context=ANY
            )
            self.assertTrue(mock_confirm.call_args[1]["context"]["send_email"])
            mock_quo_send.assert_not_called()
            env = self.env(cr)
            tx = self.tx.with_env(env)
            # check state
            self.assertEqual(
                tx.state, 'done',
                'Redsys: validation put tx into done state')
            self.assertEqual(
                tx.redsys_txnid,
                self.redsys_ds_parameters.get('Ds_AuthorisationCode'),
                'Redsys: validation did not update tx payid')

    def test_91_redsys_return_post(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(redsys.environment,
                             'test', 'test without test environment')
        res = self.data_post_redsys(url='/payment/redsys/return')
        self.assertGreater(res.url.find('/shop'), 0,
                           'Redsys: Redirection to /shop')

    def test_91_redsys_result_page(self):
        with self.cursor() as cr:
            env = self.env(cr)
            redsys = self.redsys.with_env(env)
            # be sure not to do stupid thing
            self.assertEqual(redsys.environment,
                             'test', 'test without test environment')
            sale_order_id = self.so.with_env(env).id
        self.session.sale_last_order_id = sale_order_id
        http.root.session_store.save(self.session)
        res = self.data_post_redsys(
            url='/payment/redsys/result/redsys_result_ok')
        self.assertEqual(res.code, 200)
