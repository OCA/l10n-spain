# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp
from openerp.tools.float_utils import float_compare

_logger = logging.getLogger(__name__)


class AcquirerRedsysPartial(models.Model):
    _inherit = 'payment.acquirer'

    redsys_percent_partial = fields.Float(
        string='Reduction percent', digits=dp.get_precision('Account'))

    def _prepare_merchant_parameters(self, acquirer, tx_values):
        if acquirer.redsys_percent_partial > 0:
            amount = tx_values['amount']
            tx_values['amount'] = amount - (
                amount * acquirer.redsys_percent_partial / 100)
        return super(AcquirerRedsysPartial, self)._prepare_merchant_parameters(
            acquirer, tx_values)


class TxRedsysPartial(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _redsys_form_get_invalid_parameters(self, tx, data):
        res = super(TxRedsysPartial, self)._redsys_form_get_invalid_parameters(
            tx, data)
        if tx.acquirer_id.redsys_percent_partial > 0.0:
            new_amount = tx.amount - (
                tx.amount * tx.acquirer_id.redsys_percent_partial / 100)
            for element in res:
                key, x, y = element
                if key == 'Amount':
                    if (float_compare(
                                float(element[1]) / 100, new_amount, 2) == 0):
                        res.pop(res.index(element))
        return res

    @api.model
    def form_feedback(self, data, acquirer_name):
        res = super(TxRedsysPartial, self).form_feedback(data, acquirer_name)
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
                    new_amount = tx.amount - (
                        tx.amount * percent_reduction / 100)
                    tx.amount = new_amount
                    amount_matches = (
                        tx.sale_order_id.state in ['draft', 'sent'] and
                        float_compare(new_amount, new_so_amount, 2) == 0)
                    if amount_matches:
                        if tx.state == 'done':
                            _logger.info(
                                '<%s> transaction completed, confirming order '
                                '%s (ID %s)', acquirer_name,
                                tx.sale_order_id.name, tx.sale_order_id.id)
                            self.env['sale.order'].sudo().browse(
                                tx.sale_order_id.id).with_context(
                                send_email=True).action_button_confirm()
                        elif (tx.state != 'cancel' and
                                tx.sale_order_id.state == 'draft'):
                            _logger.info('<%s> transaction pending, sending '
                                         'quote email for order %s (ID %s)',
                                         acquirer_name, tx.sale_order_id.name,
                                         tx.sale_order_id.id)
                            self.env['sale.order'].sudo().browse(
                                tx.sale_order_id.id).force_quotation_send()
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
