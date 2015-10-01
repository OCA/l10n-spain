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

from openerp import models, fields, api


class StockLocation(models.Model):
    _inherit = "stock.location"

    intrastat_state = fields.Char(
        string='State', size=2,
        help="Spain's state where the stock location is located. "
        "This parameter is required for the declaration).")

    @api.one
    @api.constrains('intrastat_state')
    def _check_intrastat_state(self):
        self.env['res.company'].real_state_check(
            self.intrastat_state)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.one
    @api.depends(
        'picking_type_id', 'move_lines', 'move_lines.location_dest_id',
        'move_lines.location_id')
    def _compute_state(self):
        intrastat_state = False
        start_point = False
        if self.move_lines:
            if (self.picking_type_id.code == 'outgoing'
                    and self.move_lines[0].location_dest_id.usage ==
                    'customer'):
                start_point = self.move_lines[0].location_id
            elif (self.picking_type_id.code == 'incoming'
                    and self.move_lines[0].location_dest_id.usage ==
                    'internal'):
                start_point = self.move_lines[0].location_dest_id
            while start_point:
                if start_point.intrastat_state:
                    intrastat_state = start_point.intrastat_state
                    break
                elif start_point.location_id:
                    start_point = start_point.location_id
                    continue
                else:
                    break
        self.intrastat_state = intrastat_state

    intrastat_transport = fields.Selection([
        (1, 'Transport maritime'),
        (2, 'Transport par chemin de fer'),
        (3, 'Transport par route'),
        (4, 'Transport par air'),
        (5, 'Envois postaux'),
        (7, 'Installations de transport fixes'),
        (8, 'Transport par navigation intérieure'),
        (9, 'Propulsion propre')], 'Type of transport',
        help="Select the type of transport of the goods. This information "
        "is required for the product intrastat report (DEB).")
    intrastat_state = fields.Char(
        compute='_compute_state', size=2, string='Intrastat State',
        help='Compute the source departement for a Delivery Order, '
        'or the destination state for an Incoming Shipment.')

    def _create_invoice_from_picking(
            self, cr, uid, picking, vals, context=None):
        '''Copy transport and state from picking to invoice'''
        vals['intrastat_transport'] = picking.intrastat_transport
        vals['intrastat_state'] = picking.intrastat_state
        if picking.partner_id and picking.partner_id.country_id:
            vals['intrastat_country_id'] = picking.partner_id.country_id.id
        return super(StockPicking, self)._create_invoice_from_picking(
            cr, uid, picking, vals, context=context)
