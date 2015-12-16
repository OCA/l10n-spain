# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

from openerp import models, fields, api
from openerp.addons import decimal_precision as dp
from openerp.tools.float_utils import float_compare


class PosOrder(models.Model):
    _inherit = 'pos.order'

    simplified = fields.Boolean(string='Simplified invoice', default=True)

    @api.one
    def action_invoice(self):
        self.simplified = False

    @api.multi
    def simplified_limit_check(self):
        for order in self:
            if not order.simplified:
                continue
            limit = order.session_id.config_id.simplified_invoice_limit
            amount_total = order.amount_total
            precision_digits = dp.get_precision('Account')(self.env.cr)[1]
            # -1 or 0: amount_total <= limit, simplified
            #       1: amount_total > limit, can not be simplified
            simplified = (
                float_compare(amount_total, limit,
                              precision_digits=precision_digits) <= 0)
            # Change simplified flag if incompatible
            if not simplified:
                order.write({'simplified': simplified})

    @api.model
    def sequence_number_sync(self, vals):
        next = vals.get('_sequence_ref_number', False)
        next = int(next) if next else False
        if vals.get('session_id') and next is not False:
            session = self.env['pos.session'].browse(vals['session_id'])
            if next != session.config_id.sequence_id.number_next_actual:
                session.config_id.sequence_id.number_next_actual = next
        if vals.get('_sequence_ref_number') is not None:
            del vals['_sequence_ref_number']

    @api.model
    def _order_fields(self, ui_order):
        vals = super(PosOrder, self)._order_fields(ui_order)
        vals['_sequence_ref_number'] = ui_order.get('sequence_ref_number')
        return vals

    @api.multi
    def write(self, vals):
        result = super(PosOrder, self).write(vals)
        self.simplified_limit_check()
        return result

    @api.model
    def create(self, vals):
        self.sequence_number_sync(vals)
        order = super(PosOrder, self).create(vals)
        order.simplified_limit_check()
        return order
