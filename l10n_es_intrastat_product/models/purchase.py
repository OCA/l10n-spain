# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def _prepare_invoice(self, cr, uid, order, line_ids, context=None):
        '''Copy country of partner_id =("origin country") and '''
        '''arrival state on invoice'''
        invoice_vals = super(PurchaseOrder, self)._prepare_invoice(
            cr, uid, order, line_ids, context=context)
        if order.partner_id.country_id:
            invoice_vals['intrastat_country_id'] = \
                order.partner_id.country_id.id
        if order.picking_ids:
            invoice_vals['intrastat_state'] = \
                order.picking_ids[0].intrastat_state
        if order.incoterm_id:
            invoice_vals['incoterm_id'] = order.incoterm_id.id
        return invoice_vals
