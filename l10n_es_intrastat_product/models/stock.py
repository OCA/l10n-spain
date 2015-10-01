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

    intrastat_department = fields.Char(
        string='Department', size=2,
        help="Spain's department where the stock location is located. "
        "This parameter is required for the declaration).")

    @api.one
    @api.constrains('intrastat_department')
    def _check_intrastat_department(self):
        self.env['res.company'].real_department_check(
            self.intrastat_department)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.one
    @api.depends(
        'picking_type_id', 'move_lines', 'move_lines.location_dest_id',
        'move_lines.location_id')
    def _compute_department(self):
        intrastat_department = False
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
                if start_point.intrastat_department:
                    intrastat_department = start_point.intrastat_department
                    break
                elif start_point.location_id:
                    start_point = start_point.location_id
                    continue
                else:
                    break
        self.intrastat_department = intrastat_department

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
    intrastat_department = fields.Char(
        compute='_compute_department', size=2, string='Intrastat Department',
        help='Compute the source departement for a Delivery Order, '
        'or the destination department for an Incoming Shipment.')

    def _create_invoice_from_picking(
            self, cr, uid, picking, vals, context=None):
        '''Copy transport and department from picking to invoice'''
        vals['intrastat_transport'] = picking.intrastat_transport
        vals['intrastat_department'] = picking.intrastat_department
        if picking.partner_id and picking.partner_id.country_id:
            vals['intrastat_country_id'] = picking.partner_id.country_id.id
        return super(StockPicking, self)._create_invoice_from_picking(
            cr, uid, picking, vals, context=context)
