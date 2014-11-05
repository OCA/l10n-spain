# -*- coding: utf-8 -*-
from hashlib import sha1
import logging
import urlparse

from openerp import models, fields, api, _
from openerp.addons.payment.models.payment_acquirer import ValidationError
from openerp.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


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
                                             ('004', 'Frances'),
                                             ], 'Merchant Consumer Language')
    redsys_pay_method = fields.Selection([('T', 'Pago con Tarjeta'),
                                          ('R', 'Pago por Transferencia'),
                                          ('D', 'Domiciliacion'),
                                          ], 'Payment Method',
                                         default='T')
    redsys_url_ok = fields.Char('URL OK')
    redsys_url_ko = fields.Char('URL KO')

    def _redsys_generate_digital_sign(self, acquirer, inout, values):
        """ Generate the shasign for incoming or outgoing communications.
        :param browse acquirer: the payment.acquirer browse record. It should
                                have a shakey in shaky out
        :param string inout: 'in' (encoding) or 'out' (decoding).
        :param dict values: transaction values

        :return string: shasign
        """
        assert acquirer.provider == 'redsys'

        def get_value(key):
            if values.get(key):
                return values[key]
            return ''

        if inout == 'out':
            keys = ['Ds_Amount',
                    'Ds_Order',
                    'Ds_MerchantCode',
                    'Ds_Currency',
                    'Ds_Response']
        else:
            keys = ['Ds_Merchant_Amount',
                    'Ds_Merchant_Order',
                    'Ds_Merchant_MerchantCode',
                    'Ds_Merchant_Currency',
                    'Ds_Merchant_TransactionType',
                    'Ds_Merchant_MerchantURL']
        sign = ''.join('%s' % (get_value(k)) for k in keys)
        # Add the pre-shared secret key at the end of the signature
        sign = sign + acquirer.redsys_secret_key
        if isinstance(sign, str):
            sign = urlparse.parse_qsl(sign)
        shasign = sha1(sign).hexdigest().upper()
        return shasign

    @api.model
    def redsys_form_generate_values(self, id, partner_values, tx_values):
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        acquirer = self.browse(id)
        redsys_tx_values = dict(tx_values)
        redsys_tx_values.update({
            'Ds_Sermepa_Url':
                (self._get_redsys_urls(acquirer.environment)
                    ['redsys_form_url']),
            'Ds_Merchant_Amount': int(tx_values['amount'] * 100),
            'Ds_Merchant_Currency': acquirer.redsys_currency or '978',
            'Ds_Merchant_Order': tx_values['reference'][:12],
            'Ds_Merchant_MerchantCode': acquirer.redsys_merchant_code[:9],
            'Ds_Merchant_Terminal': acquirer.redsys_terminal or '1',
            'Ds_Merchant_TransactionType': (
                acquirer.redsys_transaction_type or '0'),
            'Ds_Merchant_Titular': acquirer.redsys_merchant_titular[:60],
            'Ds_Merchant_MerchantName': acquirer.redsys_merchant_name[:25],
            'Ds_Merchant_MerchantURL':
                (acquirer.redsys_merchant_url
                 and acquirer.redsys_merchant_url[:250] or ''),
            'Ds_Merchant_MerchantData': acquirer.redsys_merchant_data or '',
            'Ds_Merchant_ProductDescription': (
                acquirer.redsys_merchant_description[:125]),
            'Ds_Merchant_ConsumerLanguage': (
                acquirer.redsys_merchant_lang or '001'),
            'Ds_Merchant_UrlOK': acquirer.redsys_url_ok or '',
            'Ds_Merchant_UrlKO': acquirer.redsys_url_ko or '',
            'Ds_Merchant_PayMethods': acquirer.redsys_pay_method or 'T',
        })

        redsys_tx_values['Ds_Merchant_MerchantSignature'] = (
            self._redsys_generate_digital_sign(
                acquirer, 'in', redsys_tx_values))
        return partner_values, redsys_tx_values

    @api.multi
    def redsys_get_form_action_url(self):
        return self._get_redsys_urls(self.environment)['redsys_form_url']


class TxRedsys(models.Model):
    _inherit = 'payment.transaction'

    redsys_txnid = fields.Char('Transaction ID')

    # --------------------------------------------------
    # FORM RELATED METHODS
    # --------------------------------------------------

    @api.model
    def _redsys_form_get_tx_from_data(self, data):
        """ Given a data dict coming from redsys, verify it and
        find the related transaction record. """
        reference = data.get('Ds_Order')
        pay_id = data.get('Ds_AuthorisationCode')
        shasign = data.get('Ds_Signature')
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
        acquirer = self.env['payment.acquirer']
        shasign_check = acquirer._redsys_generate_digital_sign(
            tx.acquirer_id, 'out', data)
        if shasign_check.upper() != shasign.upper():
            error_msg = 'Redsys: invalid shasign, received\ %s, computed %s,'\
                ' for data %s' % (shasign, shasign_check, data)
            _logger.error(error_msg)
            raise ValidationError(error_msg)
        return tx

    @api.model
    def _redsys_form_get_invalid_parameters(self, tx, data):
        invalid_parameters = []

        if (tx.acquirer_reference
                and data.get('Ds_Order')) != tx.acquirer_reference:
            invalid_parameters.append(
                ('Transaction Id', data.get('Ds_Order'),
                 tx.acquirer_reference))
        # check what is buyed
        if (float_compare(float(data.get('Ds_Amount', '0.0'))/100,
                          tx.amount, 2) != 0):
            invalid_parameters.append('Amount', data.get('Ds_Amount'),
                                      '%.2f' % tx.amount)
        return invalid_parameters

    @api.model
    def _redsys_form_validate(self, tx, data):
        status_code = int(data.get('Ds_Response', '29999'))
        if (status_code >= 0) and (status_code <= 99):
            tx.write({
                'state': 'done',
                'redsys_txnid': data.get('Ds_AuthorisationCode'),
                'state_message': _('Ok: %s') % data.get('Ds_Response'),
            })
            return True
        if (status_code >= 101) and (status_code <= 202):
            # 'Payment error: code: %s.'
            tx.write({
                'state': 'pending',
                'redsys_txnid': data.get('Ds_AuthorisationCode'),
                'state_message': _('Error: %s') % data.get('Ds_Response'),
            })
            return True
        if (status_code == 912) and (status_code == 9912):
            # 'Payment error: bank unavailable.'
            tx.write({
                'state': 'cancel',
                'redsys_txnid': data.get('Ds_AuthorisationCode'),
                'state_message': (_('Bank Error: %s')
                                  % data.get('Ds_Response')),
            })
            return True
        else:
            error = 'Redsys: feedback error'
            _logger.info(error)
            tx.write({
                'state': 'error',
                'redsys_txnid': data.get('Ds_AuthorisationCode'),
                'state_message': error,
            })
            return False
