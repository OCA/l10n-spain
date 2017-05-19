# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
import pprint
import werkzeug

from odoo import http
from odoo.http import request
from odoo.addons.website_sale.controllers.main import WebsiteSale

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
    ], type='http', auth='none', csrf=False)
    def redsys_return(self, **post):
        """ Redsys."""
        _logger.info('Redsys: entering form_feedback with post data %s',
                     pprint.pformat(post))
        if post:
            request.env['payment.transaction'].sudo().form_feedback(
                post, 'redsys')
        return_url = post.pop('return_url', '')
        if not return_url:
            return_url = '/shop'
        return werkzeug.utils.redirect(return_url)

    @http.route(
        ['/payment/redsys/result/<page>'], type='http', auth='public',
        methods=['GET'], website=True)
    def redsys_result(self, page, **vals):
        try:
            sale_order_id = request.session.get('sale_last_order_id')
            sale_obj = request.env['sale.order']
            order = sale_obj.sudo().browse(sale_order_id)
            res = {
                'order': order,
            }
            return request.render('payment_redsys.%s' % str(page), res)
        except:
            return request.render('website.404')


class WebsiteSaleRedsys(WebsiteSale):
    @http.route(['/shop/payment/transaction/<int:acquirer_id>'], type='json',
                auth="public", website=True)
    def payment_transaction(self, acquirer_id, tx_type='form', token=None,
                            **kwargs):
        tx_id = super(WebsiteSaleRedsys, self).payment_transaction(
            acquirer_id, tx_type, token, **kwargs)
        acquirer = request.env['payment.acquirer'].browse(acquirer_id)
        if acquirer.provider == 'redsys':
            request.env['website'].sale_reset()
        return tx_id
