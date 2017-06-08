# -*- coding: utf-8 -*-
################################################################
#    License, author and contributors information in:          #
#    __openerp__.py file at the root folder of this module.    #
################################################################

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    public_sector = fields.Boolean(string='Public Sector Works', readonly=True,
                                   states={'draft': [('readonly', False)]})
    ot_percentage = fields.Integer(string='Order Tax Percentage', default=21,
                                   readonly=True,
                                   states={'draft': [('readonly', False)]})
    ge_percentage = fields.Integer(string='General Expenses Percentage',
                                   default=13, readonly=True,
                                   states={'draft': [('readonly', False)]})
    ip_percentage = fields.Integer(string='Industrial Profit Percentage',
                                   default=6, readonly=True,
                                   states={'draft': [('readonly', False)]})
    amount_material_exe = fields.Float(
        string='Amount Material Execution', digits=dp.get_precision('Account'),
        readonly=True,
        help='Amount untaxed without general expenses neither industrial '
             'profit included.')
    general_expenses = fields.Float(
        string='General Expenses', digits=dp.get_precision('Account'),
        readonly=True, help='General expenses.')
    industrial_profit = fields.Float(
        string='Industrial Profit', digits=dp.get_precision('Account'),
        readonly=True, help='Industrial profit.')
    ge_ip_total = fields.Float(
        string='GE and IP Sum', digits=dp.get_precision('Account'),
        readonly=True, help='Sum of general expenses plus industrial profit.')

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move,
                          context=None):
        """ Modifying this to move public sector works fields from stock
        pickings to account invoices.
        """
        values = super(StockPicking, self)._get_invoice_vals(
            cr, uid, key, inv_type, journal_id, move, context=None)
        if move.picking_id and move.procurement_id.sale_line_id and \
           move.procurement_id.sale_line_id.order_id:
            picking = move.picking_id
            values.update({
                'public_sector': picking.public_sector or False,
                'ot_percentage': picking.ot_percentage or False,
                'ge_percentage': picking.ge_percentage or False,
                'ip_percentage': picking.ip_percentage or False,
                'amount_material_exe': picking.amount_material_exe or False,
                'general_expenses': picking.general_expenses or False,
                'industrial_profit': picking.industrial_profit or False,
                'ge_ip_total': picking.ge_ip_total or False,
            })
        return values


class StockMove(models.Model):
    _inherit = 'stock.move'

    def _prepare_picking_assign(self, cr, uid, move, context=None):
        """ Modifying this to move public sector works fields from sale orders
        to stock pickings.
        """
        values = super(StockMove, self)._prepare_picking_assign(
            cr, uid, move, context=None)
        if move.procurement_id and move.procurement_id.sale_line_id and \
           move.procurement_id.sale_line_id.order_id:
            sale_order = move.procurement_id.sale_line_id.order_id
            values.update({
                'public_sector': sale_order.public_sector or False,
                'ot_percentage': sale_order.ot_percentage or False,
                'ge_percentage': sale_order.ge_percentage or False,
                'ip_percentage': sale_order.ip_percentage or False,
                'amount_material_exe': sale_order.amount_material_exe or False,
                'general_expenses': sale_order.general_expenses or False,
                'industrial_profit': sale_order.industrial_profit or False,
                'ge_ip_total': sale_order.ge_ip_total or False,
            })
        return values

    @api.cr_uid_ids_context
    def _picking_assign(self, cr, uid, move_ids, procurement_group,
                        location_from, location_to, context=None):
        """ Modifying this to move carrier fields from sale orders to stock
        pickings (when user creates the stock from the sale order in a
        different way from the above method).
        """
        """Assign a picking on the given move_ids, which is a list of move
        supposed to share the same procurement_group, location_from and
        location_to (and company). Those attributes are also given as
        parameters.
        """
        pick_obj = self.pool.get("stock.picking")
        # Use a SQL query as doing with the ORM will split it in different
        # queries with id IN (,,)
        # In the next version, the locations on the picking should be stored
        # again.
        query = """
            SELECT stock_picking.id FROM stock_picking, stock_move
            WHERE
                stock_picking.state in ('draft', 'confirmed', 'waiting') AND
                stock_move.picking_id = stock_picking.id AND
                stock_move.location_id = %s AND
                stock_move.location_dest_id = %s AND
        """
        params = (location_from, location_to)
        if not procurement_group:
            query += "stock_picking.group_id IS NULL LIMIT 1"
        else:
            query += "stock_picking.group_id = %s LIMIT 1"
            params += (procurement_group,)
        cr.execute(query, params)
        [pick] = cr.fetchone() or [None]
        if not pick:
            move = self.browse(cr, uid, move_ids, context=context)[0]
            values = {
                'origin': move.origin,
                'company_id': move.company_id and move.company_id.id or False,
                'move_type': move.group_id and
                move.group_id.move_type or 'direct',
                'partner_id': move.partner_id.id or False,
                'picking_type_id': move.picking_type_id and
                move.picking_type_id.id or False,
            }
            if move.procurement_id and move.procurement_id.sale_line_id and \
               move.procurement_id.sale_line_id.order_id:
                sale_order = move.procurement_id.sale_line_id.order_id
                values.update({
                    'public_sector': sale_order.public_sector or False,
                    'ot_percentage': sale_order.ot_percentage or False,
                    'ge_percentage': sale_order.ge_percentage or False,
                    'ip_percentage': sale_order.ip_percentage or False,
                    'amount_material_exe': sale_order.amount_material_exe or
                    False,
                    'general_expenses': sale_order.general_expenses or False,
                    'industrial_profit': sale_order.industrial_profit or False,
                    'ge_ip_total': sale_order.ge_ip_total or False,
                })
            pick = pick_obj.create(cr, uid, values, context=context)
        return self.write(cr, uid, move_ids, {'picking_id': pick},
                          context=context)
