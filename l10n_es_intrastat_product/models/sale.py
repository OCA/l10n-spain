# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        '''Copy destination country and departure state on invoice'''
        invoice_vals = super(SaleOrder, self)._prepare_invoice(
            cr, uid, order, lines, context=context)
        if order.partner_shipping_id and order.partner_shipping_id.country_id:
            invoice_vals['intrastat_country_id'] = \
                order.partner_shipping_id.country_id.id
        if order.picking_ids:
            invoice_vals['intrastat_state'] = \
                order.picking_ids[0].intrastat_state
        if order.incoterm:
            invoice_vals['incoterm_id'] = order.incoterm.id
        return invoice_vals
