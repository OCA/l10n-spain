# -*- encoding: utf-8 -*-
##############################################################################
#
#    l10n Spain Report intrastat product module for Odoo
#    Copyright (C) 2010-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Ismael Calvo <ismael.calvo@factorlibre.com>
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

from openerp import models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        '''Copy destination country and departure department on invoice'''
        invoice_vals = super(SaleOrder, self)._prepare_invoice(
            cr, uid, order, lines, context=context)
        if order.partner_shipping_id and order.partner_shipping_id.country_id:
            invoice_vals['intrastat_country_id'] = \
                order.partner_shipping_id.country_id.id
        if order.picking_ids:
            invoice_vals['intrastat_department'] = \
                order.picking_ids[0].intrastat_department
        if order.incoterm:
            invoice_vals['incoterm_id'] = order.incoterm.id
        return invoice_vals
