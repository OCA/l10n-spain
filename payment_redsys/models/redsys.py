# © 2016-2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import hashlib
import hmac
import base64
import logging
import json
import urllib

from odoo import models, fields, api, _
from odoo.addons.payment.models.payment_acquirer import ValidationError
from odoo.addons import decimal_precision as dp
from odoo.tools.float_utils import float_compare
from odoo import exceptions
from odoo import http
from odoo.tools import config

_logger = logging.getLogger(__name__)

try:
    from Crypto.Cipher import DES3
except ImportError:
    _logger.info("Missing dependency (pycryptodome). See README.")


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

    provider = fields.Selection(selection_add=[('redsys', 'Redsys')])
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
    redsys_percent_partial = fields.Float(
        string='Reduction percent',
        digits=dp.get_precision('Account'),
        help='Write percent reduction payment, for this method payment.'
             'With this option you can allow partial payments in your '
             'shop online, the residual amount in pending for do a manual '
             'payment later.'
    )

    @api.constrains('redsys_percent_partial')
    def check_redsys_percent_partial(self):
        if (self.redsys_percent_partial < 0 or
                self.redsys_percent_partial > 100):
            raise exceptions.Warning(
                _('Partial payment percent must be between 0 and 100'))

    @api.model
    def _get_website_callback_url(self):
        """For force a callback url from Redsys distinct to base url website,
         only apply to a Redsys response.
        """
        get_param = self.env['ir.config_parameter'].sudo().get_param
        return get_param(
            'payment_redsys.callback_url')

    @api.model
    def _get_website_url(self):
        website_id = self.env.context.get('website_id', False)
        if website_id:
            base_url = '%s://%s' % (
                http.request.httprequest.environ['wsgi.url_scheme'],
                self.env['website'].browse(website_id).domain
            )
        else:
            get_param = self.env['ir.config_parameter'].sudo().get_param
            base_url = get_param('web.base.url')
        return base_url or ''

    def _prepare_merchant_parameters(self, tx_values):
        # Check multi-website
        base_url = self._get_website_url()
        callback_url = self._get_website_callback_url()
        if self.redsys_percent_partial > 0:
            amount = tx_values['amount']
            tx_values['amount'] = amount - (
                amount * self.redsys_percent_partial / 100)
        values = {
            'Ds_Sermepa_Url': (
                self._get_redsys_urls(self.environment)[
                    'redsys_form_url']),
            'Ds_Merchant_Amount': str(int(round(tx_values['amount'] * 100))),
            'Ds_Merchant_Currency': self.redsys_currency or '978',
            'Ds_Merchant_Order': (
                tx_values['reference'] and tx_values['reference'][-12:] or
                False),
            'Ds_Merchant_MerchantCode': (
                self.redsys_merchant_code and
                self.redsys_merchant_code[:9]),
            'Ds_Merchant_Terminal': self.redsys_terminal or '1',
            'Ds_Merchant_TransactionType': (
                self.redsys_transaction_type or '0'),
            'Ds_Merchant_Titular': (
                self.redsys_merchant_titular[:60] and
                self.redsys_merchant_titular[:60]),
            'Ds_Merchant_MerchantName': (
                self.redsys_merchant_name and
                self.redsys_merchant_name[:25]),
            'Ds_Merchant_MerchantUrl': (
                '%s/payment/redsys/return' % (callback_url or base_url))[:250],
            'Ds_Merchant_MerchantData': self.redsys_merchant_data or '',
            'Ds_Merchant_ProductDescription': (
                self._product_description(tx_values['reference']) or
                self.redsys_merchant_description and
                self.redsys_merchant_description[:125]),
            'Ds_Merchant_ConsumerLanguage': (
                self.redsys_merchant_lang or '001'),
            'Ds_Merchant_UrlOk':
            '%s/payment/redsys/result/redsys_result_ok' % base_url,
            'Ds_Merchant_UrlKo':
            '%s/payment/redsys/result/redsys_result_ko' % base_url,
            'Ds_Merchant_Paymethods': self.redsys_pay_method or 'T',
        }
        return self._url_encode64(json.dumps(values))

    def _url_encode64(self, data):
        data = base64.b64encode(data.encode())
        return data

    def _url_decode64(self, data):
        return json.loads(base64.b64decode(data).decode())

    def sign_parameters(self, secret_key, params64):
        params_dic = self._url_decode64(params64)
        if 'Ds_Merchant_Order' in params_dic:
            order = str(params_dic['Ds_Merchant_Order'])
        else:
            order = str(
                urllib.parse.unquote(params_dic.get('Ds_Order', 'Not found')))
        cipher = DES3.new(
            key=base64.b64decode(secret_key),
            mode=DES3.MODE_CBC,
            IV=b'\0\0\0\0\0\0\0\0')
        diff_block = len(order) % 8
        zeros = diff_block and (b'\0' * (8 - diff_block)) or b''
        key = cipher.encrypt(str.encode(order + zeros.decode()))
        if isinstance(params64, str):
            params64 = params64.encode()
        dig = hmac.new(
            key=key,
            msg=params64,
            digestmod=hashlib.sha256).digest()
        return base64.b64encode(dig).decode()

    @api.multi
    def redsys_form_generate_values(self, values):
        self.ensure_one()
        redsys_tx = self.env['payment.transaction'].search([
            ('reference', '=', values['reference'])
        ])
        if redsys_tx and not config['test_enable']:
            reference = self.env['ir.sequence'].next_by_code(
                'payment.transaction')
            redsys_tx.write({'reference': reference})
            values.update({'reference': reference})
        redsys_values = dict(values)
        merchant_parameters = self._prepare_merchant_parameters(values)
        redsys_values.update({
            'Ds_SignatureVersion': str(self.redsys_signature_version),
            'Ds_MerchantParameters': merchant_parameters,
            'Ds_Signature': self.sign_parameters(
                self.redsys_secret_key, merchant_parameters),
        })
        return redsys_values

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
        parameters = data.get('Ds_MerchantParameters', '')
        return json.loads(base64.b64decode(parameters).decode())

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _redsys_form_get_tx_from_data(self, data):
        """ Given a data dict coming from redsys, verify it and
        find the related transaction record. """
        parameters = data.get('Ds_MerchantParameters', '')
        parameters_dic = json.loads(base64.b64decode(parameters).decode())
        reference = urllib.parse.unquote(parameters_dic.get('Ds_Order', ''))
        pay_id = parameters_dic.get('Ds_AuthorisationCode')
        shasign = data.get(
            'Ds_Signature', '').replace('_', '/').replace('-', '+')
        test_env = http.request.session.get('test_enable', False)
        if not reference or not pay_id or not shasign:
            error_msg = 'Redsys: received data with missing reference' \
                ' (%s) or pay_id (%s) or shashign (%s)' % (reference,
                                                           pay_id, shasign)
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
            # For tests
            http.OpenERPSession.tx_error = True
        tx = self.search([('reference', '=', reference)])
        if not tx or len(tx) > 1:
            error_msg = 'Redsys: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
            # For tests
            http.OpenERPSession.tx_error = True
        if tx and not test_env:
            # verify shasign
            shasign_check = tx.acquirer_id.sign_parameters(
                tx.acquirer_id.redsys_secret_key, parameters)
            if shasign_check != shasign:
                error_msg = (
                    'Redsys: invalid shasign, received %s, computed %s, '
                    'for data %s' % (shasign, shasign_check, data)
                )
                _logger.info(error_msg)
                raise ValidationError(error_msg)
        return tx

    @api.multi
    def _redsys_form_get_invalid_parameters(self, data):
        test_env = http.request.session.get('test_enable', False)
        invalid_parameters = []
        parameters_dic = self.merchant_params_json2dict(data)
        if (self.acquirer_reference and
                parameters_dic.get('Ds_Order')) != self.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', parameters_dic.get('Ds_Order'),
                 self.acquirer_reference))

        # check what is buyed
        if self.acquirer_id.redsys_percent_partial > 0.0:
            new_amount = self.amount - (
                self.amount * self.acquirer_id.redsys_percent_partial / 100)
            self.amount = new_amount

        if (float_compare(float(parameters_dic.get('Ds_Amount', '0.0')) / 100,
                          self.amount, 2) != 0):
            invalid_parameters.append(
                ('Amount', parameters_dic.get('Ds_Amount'),
                 '%.2f' % self.amount))

        if invalid_parameters and test_env:
            # If transaction is in test mode invalidate invalid_parameters
            # to avoid logger error from parent method
            return []
        return invalid_parameters

    @api.model
    def _get_redsys_state(self, status_code):
        if 0 <= status_code <= 100:
            return "done"
        elif status_code <= 203:
            return "pending"
        elif 912 <= status_code <= 9912:
            return "cancel"
        else:
            return "error"

    def _redsys_form_validate(self, data):
        params = self.merchant_params_json2dict(data)
        status_code = int(params.get('Ds_Response', '29999'))
        state = self._get_redsys_state(status_code)
        vals = {
            'state': state,
            'redsys_txnid': params.get('Ds_AuthorisationCode'),
        }
        state_message = ""
        if state == 'done':
            vals['state_message'] = _('Ok: %s') % params.get('Ds_Response')
        elif state == 'pending':  # 'Payment error: code: %s.'
            state_message = _('Error: %s (%s)')
        elif state == 'cancel':  # 'Payment error: bank unavailable.'
            state_message = _('Bank Error: %s (%s)')
        else:
            state_message = _('Redsys: feedback error %s (%s)')
        if state_message:
            vals['state_message'] = state_message % (
                params.get('Ds_Response'), params.get('Ds_ErrorCode'),
            )
            if state == 'error':
                _logger.warning(vals['state_message'])
        self.write(vals)
        return state != 'error'

    @api.model
    def form_feedback(self, data, acquirer_name):
        res = super(TxRedsys, self).form_feedback(data, acquirer_name)
        try:
            tx_find_method_name = '_%s_form_get_tx_from_data' % acquirer_name
            if hasattr(self, tx_find_method_name):
                tx = getattr(self, tx_find_method_name)(data)
            _logger.info(
                '<%s> transaction processed: tx ref:%s, tx amount: %s',
                acquirer_name, tx.reference if tx else 'n/a',
                tx.amount if tx else 'n/a')
            if tx.acquirer_id.redsys_percent_partial > 0:
                if tx and tx.sale_order_id:
                    percent_reduction = tx.acquirer_id.redsys_percent_partial
                    new_so_amount = (
                        tx.sale_order_id.amount_total - (
                            tx.sale_order_id.amount_total *
                            percent_reduction / 100))
                    amount_matches = (
                        tx.sale_order_id.state in ['draft', 'sent'] and
                        float_compare(tx.amount, new_so_amount, 2) == 0)
                    if amount_matches:
                        if tx.state == 'done':
                            _logger.info(
                                '<%s> transaction completed, confirming order '
                                '%s (ID %s)', acquirer_name,
                                tx.sale_order_id.name, tx.sale_order_id.id)
                            if not self.env.context.get('bypass_test', False):
                                tx.sale_order_id.with_context(
                                    send_email=True).action_confirm()
                        elif (tx.state != 'cancel' and
                                tx.sale_order_id.state == 'draft'):
                            _logger.info('<%s> transaction pending, sending '
                                         'quote email for order %s (ID %s)',
                                         acquirer_name, tx.sale_order_id.name,
                                         tx.sale_order_id.id)
                            if not self.env.context.get('bypass_test', False):
                                tx.sale_order_id.force_quotation_send()
                    else:
                        _logger.warning('<%s> transaction MISMATCH for order '
                                        '%s (ID %s)', acquirer_name,
                                        tx.sale_order_id.name,
                                        tx.sale_order_id.id)
        except Exception:
            _logger.exception(
                'Fail to confirm the order or send the confirmation email%s',
                tx and ' for the transaction %s' % tx.reference or '')
        return res

    def _confirm_so(self):
        if (self.state == 'pending' and self.sale_order_id.state == 'draft' and
                self.acquirer_id.provider == 'redsys'):
            _logger.info(
                '<%s> transaction not processed for order %s (ID %s)',
                self.acquirer_id.provider, self.sale_order_id.name,
                self.sale_order_id.id)
            return False
        else:
            return super()._confirm_so()
