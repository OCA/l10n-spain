# -*- coding: utf-8 -*-
import hashlib
import hmac
import base64
import logging
import json

from openerp import models, fields, api, _
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.tools.float_utils import float_compare
_logger = logging.getLogger(__name__)

try:
    from Crypto.Cipher import DES3
except ImportError:
    _logger.info("Missing dependency (pycrypto). See README.")


class AcquirerRedsys(models.Model):
    _inherit = 'payment.acquirer'

    def _get_redsys_urls(self, environment):
        """ Redsys URLs
        """
        if environment == 'prod':
            return {
                'redsys_form_url':
                'https://sis.redsys.es/sis/realizarPago/',
            }
        else:
            return {
                'redsys_form_url':
                'https://sis-t.redsys.es:25443/sis/realizarPago/',
            }

    @api.model
    def _get_providers(self):
        providers = super(AcquirerRedsys, self)._get_providers()
        providers.append(['redsys', 'Redsys'])
        return providers

    redsys_merchant_url = fields.Char('Merchant URL',
                                      required_if_provider='redsys')
    redsys_merchant_name = fields.Char('Merchant Name',
                                       required_if_provider='redsys')
    redsys_merchant_titular = fields.Char('Merchant Titular',
                                          required_if_provider='redsys')
    redsys_merchant_code = fields.Char('Merchant code',
                                       required_if_provider='redsys')
    redsys_merchant_description = fields.Char('Product Description',
                                              required_if_provider='redsys')
    redsys_secret_key = fields.Char('Secret Key',
                                    required_if_provider='redsys')
    redsys_terminal = fields.Char('Terminal', default='1',
                                  required_if_provider='redsys')
    redsys_currency = fields.Char('Currency', default='978',
                                  required_if_provider='redsys')
    redsys_transaction_type = fields.Char('Transtaction Type', default='0',
                                          required_if_provider='redsys')
    redsys_merchant_data = fields.Char('Merchant Data')
    redsys_merchant_lang = fields.Selection([('001', 'Castellano'),
                                             ('002', 'Inglés'),
                                             ('003', 'Catalán'),
                                             ('004', 'Francés'),
                                             ('005', 'Alemán'),
                                             ('006', 'Holandés'),
                                             ('007', 'Italiano'),
                                             ('008', 'Sueco'),
                                             ('009', 'Portugués'),
                                             ('010', 'Valenciano'),
                                             ('011', 'Polaco'),
                                             ('012', 'Gallego'),
                                             ('013', 'Euskera'),
                                             ], 'Merchant Consumer Language',
                                            default='001')
    redsys_pay_method = fields.Selection([('T', 'Pago con Tarjeta'),
                                          ('R', 'Pago por Transferencia'),
                                          ('D', 'Domiciliacion'),
                                          ], 'Payment Method',
                                         default='T')
    redsys_signature_version = fields.Selection(
        [('HMAC_SHA256_V1', 'HMAC SHA256 V1')], default='HMAC_SHA256_V1')
    send_quotation = fields.Boolean('Send quotation', default=True)

    def _prepare_merchant_parameters(self, acquirer, tx_values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        sale_order = self.env['sale.order'].search(
            [('name', '=', tx_values['reference'])])
        values = {
            'Ds_Sermepa_Url': (
                self._get_redsys_urls(acquirer.environment)[
                    'redsys_form_url']),
            'Ds_Merchant_Amount': str(int(round(tx_values['amount'] * 100))),
            'Ds_Merchant_Currency': acquirer.redsys_currency or '978',
            'Ds_Merchant_Order': (
                tx_values['reference'] and tx_values['reference'][-12:] or
                False),
            'Ds_Merchant_MerchantCode': (
                acquirer.redsys_merchant_code and
                acquirer.redsys_merchant_code[:9]),
            'Ds_Merchant_Terminal': acquirer.redsys_terminal or '1',
            'Ds_Merchant_TransactionType': (
                acquirer.redsys_transaction_type or '0'),
            'Ds_Merchant_Titular': (
                acquirer.redsys_merchant_titular[:60] and
                acquirer.redsys_merchant_titular[:60]),
            'Ds_Merchant_MerchantName': (
                acquirer.redsys_merchant_name and
                acquirer.redsys_merchant_name[:25]),
            'Ds_Merchant_MerchantUrl': (
                acquirer.redsys_merchant_url and
                acquirer.redsys_merchant_url[:250] or ''),
            'Ds_Merchant_MerchantData': acquirer.redsys_merchant_data or '',
            'Ds_Merchant_ProductDescription': (
                self._product_description(tx_values['reference']) or
                acquirer.redsys_merchant_description and
                acquirer.redsys_merchant_description[:125]),
            'Ds_Merchant_ConsumerLanguage': (
                acquirer.redsys_merchant_lang or '001'),
            'Ds_Merchant_UrlOk':
            '%s/payment/redsys/result/redsys_result_ok?order_id=%s' % (
                base_url, sale_order.id),
            'Ds_Merchant_UrlKo':
            '%s/payment/redsys/result/redsys_result_ko?order_id=%s' % (
                base_url, sale_order.id),
            'Ds_Merchant_Paymethods': acquirer.redsys_pay_method or 'T',
        }
        return self._url_encode64(json.dumps(values))

    def _url_encode64(self, data):
        data = unicode(base64.encodestring(data), 'utf-8')
        return ''.join(data.splitlines())

    def _url_decode64(self, data):
        return json.loads(base64.b64decode(data))

    def sign_parameters(self, secret_key, params64):
        params_dic = self._url_decode64(params64)
        if 'Ds_Merchant_Order' in params_dic:
            order = str(params_dic['Ds_Merchant_Order'])
        else:
            order = str(params_dic.get('Ds_Order', 'Not found'))
        cipher = DES3.new(
            key=base64.b64decode(secret_key),
            mode=DES3.MODE_CBC,
            IV=b'\0\0\0\0\0\0\0\0')
        diff_block = len(order) % 8
        zeros = diff_block and (b'\0' * (8 - diff_block)) or ''
        key = cipher.encrypt(order + zeros.encode('UTF-8'))
        dig = hmac.new(
            key=key,
            msg=params64,
            digestmod=hashlib.sha256).digest()
        return self._url_encode64(dig)

    @api.model
    def redsys_form_generate_values(self, id, partner_values, tx_values):
        acquirer = self.browse(id)
        redsys_tx_values = dict(tx_values)

        merchant_parameters = self._prepare_merchant_parameters(
            acquirer, tx_values)
        redsys_tx_values.update({
            'Ds_SignatureVersion': str(acquirer.redsys_signature_version),
            'Ds_MerchantParameters': merchant_parameters,
            'Ds_Signature': self.sign_parameters(
                acquirer.redsys_secret_key, merchant_parameters),
        })
        return partner_values, redsys_tx_values

    @api.multi
    def redsys_get_form_action_url(self):
        return self._get_redsys_urls(self.environment)['redsys_form_url']

    def _product_description(self, order_ref):
        sale_order = self.env['sale.order'].search([('name', '=', order_ref)])
        res = ''
        if sale_order:
            description = '|'.join(x.name for x in sale_order.order_line)
            res = description[:125]
        return res


class TxRedsys(models.Model):
    _inherit = 'payment.transaction'

    redsys_txnid = fields.Char('Transaction ID')

    def merchant_params_json2dict(self, data):
        parameters = data.get('Ds_MerchantParameters', '').decode('base64')
        return json.loads(parameters)

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _redsys_form_get_tx_from_data(self, data):
        """ Given a data dict coming from redsys, verify it and
        find the related transaction record. """
        parameters = data.get('Ds_MerchantParameters', '')
        parameters_dic = json.loads(base64.b64decode(parameters))
        reference = parameters_dic.get('Ds_Order', '')
        pay_id = parameters_dic.get('Ds_AuthorisationCode')
        shasign = data.get(
            'Ds_Signature', '').replace('_', '/').replace('-', '+')

        if not reference or not pay_id or not shasign:
            error_msg = 'Redsys: received data with missing reference' \
                ' (%s) or pay_id (%s) or shashign (%s)' % (reference,
                                                           pay_id, shasign)
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Redsys: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            _logger.error(error_msg)
            raise ValidationError(error_msg)

        # verify shasign
        shasign_check = tx.acquirer_id.sign_parameters(
            tx.acquirer_id.redsys_secret_key, parameters)
        if shasign_check != shasign:
            error_msg = 'Redsys: invalid shasign, received %s, computed %s,' \
                ' for data %s' % (shasign, shasign_check, data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx

    @api.model
    def _redsys_form_get_invalid_parameters(self, tx, data):
        invalid_parameters = []
        parameters_dic = self.merchant_params_json2dict(data)
        if (tx.acquirer_reference and
                parameters_dic.get('Ds_Order')) != tx.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', parameters_dic.get('Ds_Order'),
                 tx.acquirer_reference))
        # check what is buyed
        if (float_compare(float(parameters_dic.get('Ds_Amount', '0.0')) / 100,
                          tx.amount, 2) != 0):
            invalid_parameters.append(
                ('Amount', parameters_dic.get('Ds_Amount'),
                 '%.2f' % tx.amount))
        return invalid_parameters

    @api.model
    def _redsys_form_validate(self, tx, data):
        parameters_dic = self.merchant_params_json2dict(data)
        status_code = int(parameters_dic.get('Ds_Response', '29999'))
        if (status_code >= 0) and (status_code <= 99):
            tx.write({
                'state': 'done',
                'redsys_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': _('Ok: %s') % parameters_dic.get(
                    'Ds_Response'),
            })
            if tx.acquirer_id.send_quotation:
                tx.sale_order_id.force_quotation_send()
            return True
        if (status_code >= 101) and (status_code <= 202):
            # 'Payment error: code: %s.'
            tx.write({
                'state': 'pending',
                'redsys_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': _('Error: %s (%s)') % (
                    parameters_dic.get('Ds_Response'),
                    parameters_dic.get('Ds_ErrorCode')
                ),
            })
            return True
        if (status_code == 912) and (status_code == 9912):
            # 'Payment error: bank unavailable.'
            tx.write({
                'state': 'cancel',
                'redsys_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': _('Bank Error: %s (%s)') % (
                    parameters_dic.get('Ds_Response'),
                    parameters_dic.get('Ds_ErrorCode')
                ),
            })
            return True
        else:
            error = _('Redsys: feedback error %s (%s)') % (
                parameters_dic.get('Ds_Response'),
                parameters_dic.get('Ds_ErrorCode')
            )
            _logger.info(error)
            tx.write({
                'state': 'error',
                'redsys_txnid': parameters_dic.get('Ds_AuthorisationCode'),
                'state_message': error,
            })
            return False
