# -*- coding: utf-8 -*-
# © 2016 - FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, fields, api


class StockLocation(models.Model):
    _inherit = "stock.location"

    intrastat_state = fields.Char(
        string='State', size=2,
        help="Spain's state where the stock location is located. "
        "This parameter is required for the declaration).")


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
            if self.picking_type_id.code == 'outgoing' \
                    and self.move_lines[0].location_dest_id.usage == \
                    'customer':
                start_point = self.move_lines[0].location_id
            elif self.picking_type_id.code == 'incoming' \
                    and self.move_lines[0].location_dest_id.usage == \
                    'internal':
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

    intrastat_transport = fields.Many2one(
        'res.country.state', 'Type of transport',
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
