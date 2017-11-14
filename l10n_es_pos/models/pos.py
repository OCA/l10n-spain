# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright 2017 - Aselcis Consulting (http://www.aselcis.com)
#                   - David Gómez <david.gomez@aselcis.com>
#                   - Miguel Paraíso <miguel.paraiso@aselcis.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import models, fields, api, _
import odoo.addons.decimal_precision as dp
from odoo.tools import float_compare
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = 'pos.order'

    simplified_invoice = fields.Char('Simplified invoice', copy=False)

    @api.model
    def simplified_limit_check(self, pos_order):
        limit = self.env['pos.session'].browse(
            pos_order['pos_session_id']).config_id.simplified_invoice_limit
        precision_digits = dp.get_precision('Account')(self.env.cr)[1]
        # -1 or 0: amount_total <= limit, simplified
        #       1: amount_total > limit, can not be simplified
        return float_compare(pos_order['amount_total'], limit,
                             precision_digits=precision_digits) < 0

    @api.model
    def _process_order(self, pos_order):
        order = super(PosOrder, self)._process_order(pos_order)
        simplified = self.simplified_limit_check(pos_order)
        if simplified:
            config = order.session_id.config_id
            if config.simple_invoice_prefix:
                config.set_next_simple_invoice_number(
                    pos_order.get('simplified_invoice',
                                  config.simple_invoice_prefix + '1'))
                order.write({
                    'simplified_invoice': pos_order.get('simplified_invoice', ''),
                })
            else:
                raise UserError(_('You need to define a simplified invoice '
                                  'prefix.'))
        return order


class PosConfig(models.Model):
    _inherit = 'pos.config'

    simple_invoice_prefix = fields.Char('Sim.Inv prefix', copy=False)
    simple_invoice_padding = fields.Integer('Sim.Inv padding', default=4)
    simple_invoice_number = fields.Integer('Sim.Inv number', default=0,
                                           copy=False, readonly=True)
    simplified_invoice_limit = fields.Float(string='Sim.Inv limit amount',
                                            digits=dp.get_precision('Account'),
                                            help='Over this amount is not '
                                                 'legally possible to create a '
                                                 'simplified invoice',
                                            default=3000)

    @api.model
    def create(self, vals):
        self.check_simple_inv_prefix(vals.get('simple_invoice_prefix', False))
        return super(PosConfig, self).create(vals)

    @api.multi
    def write(self, vals):
        self.check_simple_inv_prefix(vals.get('simple_invoice_prefix', False))
        return super(PosConfig, self).write(vals)

    def check_simple_inv_prefix(self, prefix):
        if prefix:
            configs = self.search([('simple_invoice_prefix', '=', prefix)])
            if len(configs) > 0:
                raise UserError(_(
                    'Already exists other POS config with the same Sim.Inv '
                    'prefix. You should change this field value.'))

    def set_next_simple_invoice_number(self, order_number):
        # Fix generated orders with empty simplified invoice prefix
        if 'false' in order_number:
            order_number = order_number.replace('false',
                                                self.simple_invoice_prefix)
        number = int(order_number.replace(self.simple_invoice_prefix, ''))
        if number > self.simple_invoice_number:
            self.write({'simple_invoice_number': number})
