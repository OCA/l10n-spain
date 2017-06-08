# -*- coding: utf-8 -*-
################################################################
#    License, author and contributors information in:          #
#    __openerp__.py file at the root folder of this module.    #
################################################################

from openerp import models


class SaleOrderLineMakeInvoice(models.TransientModel):
    _inherit = 'sale.order.line.make.invoice'

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        # Preserve public sector works fields from sale order to account
        # invoice (case: some lines of the sale order)
        values = super(SaleOrderLineMakeInvoice, self)._prepare_invoice(
            cr, uid, order, lines, context)
        values.update({
            'public_sector': order.public_sector or False,
            'ot_percentage': order.ot_percentage or False,
            'ge_percentage': order.ge_percentage or False,
            'ip_percentage': order.ip_percentage or False,
            'amount_material_exe': order.amount_material_exe or False,
            'general_expenses': order.general_expenses or False,
            'industrial_profit': order.industrial_profit or False,
            'ge_ip_total': order.ge_ip_total or False,
        })
        return values
