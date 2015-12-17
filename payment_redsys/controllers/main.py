# -*- coding: utf-8 -*-
import logging
import pprint
import werkzeug

from openerp import http, SUPERUSER_ID
from openerp.http import request
from openerp.addons.website_sale.controllers.main import website_sale

_logger = logging.getLogger(__name__)


class RedsysController(http.Controller):
    _return_url = '/payment/redsys/return'
    _cancel_url = '/payment/redsys/cancel'
    _exception_url = '/payment/redsys/error'
    _reject_url = '/payment/redsys/reject'

    @http.route([
        '/payment/redsys/return',
        '/payment/redsys/cancel',
        '/payment/redsys/error',
        '/payment/redsys/reject',
    ], type='http', auth='none')
    def redsys_return(self, **post):
        """ Redsys."""
        _logger.info('Redsys: entering form_feedback with post data %s',
                     pprint.pformat(post))
        if post:
            request.registry['payment.transaction'].form_feedback(
                request.cr, SUPERUSER_ID, post, 'redsys',
                context=request.context)
        return_url = post.pop('return_url', '')
        if not return_url:
            return_url = '/shop'
        return werkzeug.utils.redirect(return_url)

    @http.route(
        ['/payment/redsys/result/<page>'], type='http', auth='user',
        methods=['GET'], website=True)
    def redsys_result(self, page, **vals):
        try:
            order_id = vals.get('order_id', 0)
            sale_obj = request.env['sale.order']
            order = sale_obj.browse(int(order_id))
            res = {
                'order': order,
            }
            return request.render('payment_redsys.%s' % str(page), res)
        except:
            return request.render('website.404')


class WebsiteSale(website_sale):
    @http.route(['/shop/payment/transaction/<int:acquirer_id>'], type='json',
                auth="public", website=True)
    def payment_transaction(self, acquirer_id):
        tx_id = super(WebsiteSale, self).payment_transaction(acquirer_id)
        cr, context = request.cr, request.context
        acquirer_obj = request.registry.get('payment.acquirer')
        acquirer = acquirer_obj.browse(
            cr, SUPERUSER_ID, acquirer_id, context=context)
        if acquirer.provider == 'redsys':
            request.website.sale_reset(context=request.context)
        return tx_id
