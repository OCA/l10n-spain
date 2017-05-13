# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import objectify
import json

from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons.payment.tests.common import PaymentAcquirerCommon
from odoo.tools import mute_logger


class RedsysCommon(PaymentAcquirerCommon):

    def setUp(self):
        super(RedsysCommon, self).setUp()
        self.redsys = self.env.ref('payment_redsys.payment_acquirer_redsys')
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
        self.tx = self.env['payment.transaction'].create(self.vals_tx)


class RedsysForm(RedsysCommon):

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
        tree = objectify.fromstring(res)
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
        values = self.redsys.redsys_form_generate_values(self.vals_tx)
        self.assertEqual(
            values['Ds_Signature'],
            't5P4W9AO7QWj4WsJzXbmpbKtaa8wRgAWl32j9gPPhJQ=',
            'Redsys: Sign failed')

    def test_20_redsys_form_management(self):
        # be sure not to do stupid thing
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')

        DS_parameters = self.redsys._url_encode64(
            json.dumps(self.redsys_ds_parameters))

        # typical data posted by redsys after client has successfully paid
        redsys_post_data = {
            'Ds_Signature': '5PmN2yITrEFS/TkdL1d27DOWgaIE/AaB/NPu6AwtjHM=',
            'Ds_MerchantParameters': DS_parameters,
            'Ds_SignatureVersion': u'HMAC_SHA256_V1',
        }
        # Get transaction
        tx = self.tx._redsys_form_get_tx_from_data(redsys_post_data)
        self.assertEqual(
            tx.reference,
            'TST0001',
            'Redsys: Get transaction')

        # validate it
        self.tx.form_feedback(redsys_post_data, 'redsys')

        # check state
        self.assertEqual(
            self.tx.state, 'done',
            'Redsys: validation did not put tx into done state')
        self.assertEqual(
            self.tx.redsys_txnid,
            self.redsys_ds_parameters.get('Ds_AuthorisationCode'),
            'Redsys: validation did not update tx payid')

    @mute_logger(
        'odoo.addons.payment_redsys.models.payment', 'ValidationError')
    def test_30_redsys_form_management(self):
        # be sure not to do stupid thing
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')

        unknow_tx = self.redsys_ds_parameters.copy()
        unknow_tx['Ds_Order'] = '22'
        DS_parameters = self.redsys._url_encode64(json.dumps(unknow_tx))

        # typical data posted by redsys after client has successfully paid
        redsys_post_data = {
            'Ds_Signature': '5PmN2yITrEFS/TkdL1d27DOWgaIE/AaB/NPu6AwtjHM=',
            'Ds_MerchantParameters': DS_parameters,
            'Ds_SignatureVersion': u'HMAC_SHA256_V1',
        }

        # should raise error about unknown tx
        with self.assertRaises(ValidationError):
            self.env['payment.transaction'].form_feedback(
                redsys_post_data, 'redsys')

    def test_40_redsys_form_done(self):
        # be sure not to do stupid thing
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')

        # Force error from provider
        error_tx = self.redsys_ds_parameters.copy()
        error_tx['Ds_Response'] = '99'
        DS_parameters = self.redsys._url_encode64(json.dumps(error_tx))

        # typical data posted by redsys after client has successfully paid
        redsys_post_data = {
            'Ds_Signature': 'dPD0ByD/YLXNyy0FKQNVyFP4beWGN+ypQW73KqswAwU=',
            'Ds_MerchantParameters': DS_parameters,
            'Ds_SignatureVersion': u'HMAC_SHA256_V1',
        }

        # Get transaction
        tx = self.tx._redsys_form_get_tx_from_data(redsys_post_data)
        tx._redsys_form_validate(redsys_post_data)
        self.assertEqual(
            tx.state, 'done',
            'Redsys: validation did not put tx into done state')

    def test_50_redsys_form_pending(self):
        # be sure not to do stupid thing
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')

        # Force error from provider
        error_tx = self.redsys_ds_parameters.copy()
        error_tx['Ds_Response'] = '110'
        DS_parameters = self.redsys._url_encode64(json.dumps(error_tx))

        # typical data posted by redsys after client has successfully paid
        redsys_post_data = {
            'Ds_Signature': '2pSk3Z5XzLM1H/Mcrphzj3mtEDEcC7exrg3Fv+rVY10=',
            'Ds_MerchantParameters': DS_parameters,
            'Ds_SignatureVersion': u'HMAC_SHA256_V1',
        }

        # Get transaction
        tx = self.tx._redsys_form_get_tx_from_data(redsys_post_data)
        tx._redsys_form_validate(redsys_post_data)
        self.assertEqual(
            tx.state, 'pending',
            'Redsys: validation did not put tx into pending state')

    def test_60_redsys_form_cancel(self):
        # be sure not to do stupid thing
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')

        # Force error from provider
        error_tx = self.redsys_ds_parameters.copy()
        error_tx['Ds_Response'] = '912'
        DS_parameters = self.redsys._url_encode64(json.dumps(error_tx))

        # typical data posted by redsys after client has successfully paid
        redsys_post_data = {
            'Ds_Signature': 'q2YGZwpRi0tiT86L/DDypjIN6HeGTbiUqBPPYOMfxr8=',
            'Ds_MerchantParameters': DS_parameters,
            'Ds_SignatureVersion': u'HMAC_SHA256_V1',
        }

        # Get transaction
        tx = self.tx._redsys_form_get_tx_from_data(redsys_post_data)
        tx._redsys_form_validate(redsys_post_data)
        self.assertEqual(
            tx.state, 'cancel',
            'Redsys: validation did not put tx into cancel state')

    def test_70_redsys_form_error(self):
        # be sure not to do stupid thing
        self.assertEqual(
            self.redsys.environment, 'test', 'test without test environment')

        # Force error from provider
        error_tx = self.redsys_ds_parameters.copy()
        error_tx['Ds_Response'] = '9094'
        DS_parameters = self.redsys._url_encode64(json.dumps(error_tx))

        # typical data posted by redsys after client has successfully paid
        redsys_post_data = {
            'Ds_Signature': '9BFuTbffCfLxPkdOjRLxEYxSMCdkXWjKgTgvwfmemvM=',
            'Ds_MerchantParameters': DS_parameters,
            'Ds_SignatureVersion': u'HMAC_SHA256_V1',
        }

        # Get transaction
        tx = self.tx._redsys_form_get_tx_from_data(redsys_post_data)
        tx._redsys_form_validate(redsys_post_data)
        self.assertEqual(
            tx.state, 'error',
            'Redsys: validation did not put tx into error state')
