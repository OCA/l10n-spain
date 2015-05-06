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

    @api.multi
    def write(self, vals):
        result = super(PosOrder, self).write(vals)
        self.simplified_limit_check()
        return result

    @api.model
    def create(self, vals):
        order = super(PosOrder, self).create(vals)
        order.simplified_limit_check()
        return order
