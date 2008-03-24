#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import netsvc
from osv import fields, osv
import ir
from mx import DateTime
from tools import config

class sale_order(osv.osv):

    def _get_picking_ids(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for order in self.pool.get('sale.order').browse(cr, uid, ids, context={}):
            res[order.id]=[]
            for line in order.order_line:
                for move in line.move_ids:
                    if move.picking_id.id not in res[order.id]:
                        res[order.id].append(move.picking_id.id)
        # res example: {2: [], 4: [7], 5: [8], 6: [9], 7: [10, 11, 12, 13]}
        return res

    _inherit = "sale.order"
    _columns = {
        'picking_ids': fields.function(_get_picking_ids, method=True, string='Related Packings', type="one2many", relation='stock.picking'),
        'order_policy': fields.selection([
            ('prepaid','Invoice before delivery'),
            ('manual','Shipping & Manual Invoice'),
            ('postpaid','Automatic Invoice after delivery'),
            ('picking','Invoice from the packings'),
            ('allmanual','Manual shipping and invoice'),
        ], 'Shipping Policy', required=True, readonly=True, states={'draft':[('readonly',False)]},),
                }
                
    _defaults = {
        'order_policy': lambda *a: 'allmanual',
                }
                
    def action_ship_activity(self, cr, uid, ids, *args):
        if len(ids) > 1:
            for order in self.browse(cr, uid, ids, context={}):
                if order.order_policy <> 'allmanual':
                    return True
            self.action_ship_create(cr, uid, ids, *args)
        else:
            for order in self.browse(cr, uid, ids, context={}):
                if order.order_policy <> 'allmanual':
                    self.action_ship_create(cr, uid, ids, *args)   
                
    def action_ship_create(self, cr, uid, ids, *args, **argv):
        # args: Group or not picking. Ej: (0,) 
        # argv: Picking from lines. Ej: {'lines_ids': {2: [1], 3: [2, 3]}}
        picking_id=False
        for order in self.browse(cr, uid, ids, context={}):
            output_id = order.shop_id.warehouse_id.lot_output_id.id
            if args and (args[0] == 0): # Agrupa o no los albaranes
                picking_id = False
            if argv and (len(argv['lines_ids'])>0): # Picking from sale order lines
                lines_ids = argv['lines_ids'][order.id]
                browse_lines = self.pool.get('sale.order.line').browse(cr, uid, lines_ids, context={})    
            else:
                browse_lines = order.order_line # Picking from sale order
            for line in browse_lines:
                proc_id=False
                date_planned = (DateTime.now() + DateTime.RelativeDateTime(days=line.delay or 0.0)).strftime('%Y-%m-%d')
                if line.state == 'done':
                    continue
                if line.product_id and line.product_id.product_tmpl_id.type in ('product', 'consu'):
                    location_id = order.shop_id.warehouse_id.lot_stock_id.id
                    if not picking_id: # Create new picking
                        loc_dest_id = order.partner_id.property_stock_customer.id
                        picking_id = self.pool.get('stock.picking').create(cr, uid, {
                            'origin': order.name,
                            'type': 'out',
                            'state': 'auto',
                            'move_type': order.picking_policy,
                            'loc_move_id': loc_dest_id,
                            'sale_id': order.id,
                            'address_id': order.partner_shipping_id.id,
                            'note': order.note,
                            #'invoice_state': (order.order_policy=='picking' and '2binvoiced') or 'none',
                            'invoice_state': (order.order_policy in ('picking', 'allmanual') and '2binvoiced') or 'none',
                        })

                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name': line.name[:64],
                        'picking_id': picking_id,
                        'product_id': line.product_id.id,
                        'date_planned': date_planned,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos_qty,
                        'product_uos': (line.product_uos and line.product_uos.id)\
                                or line.product_uom.id,
                        'product_packaging' : line.product_packaging.id,
                        'address_id' : line.address_allotment_id.id or order.partner_shipping_id.id,
                        'location_id': location_id,
                        'location_dest_id': output_id,
                        'sale_line_id': line.id,
                        #'sale_line_ids':[(6,0,[line.id])],
                        'tracking_id': False,
                        'state': 'waiting',
                        'note': line.notes,
                    })
                    proc_id = self.pool.get('mrp.procurement').create(cr, uid, {
                        'name': order.name,
                        'origin': order.name,
                        'date_planned': date_planned,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                        'procure_method': line.type,
                        'move_id': move_id,
                        'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                    })
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
                    #self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                    self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id, 'state':'done'})
                elif line.product_id and line.product_id.product_tmpl_id.type=='service':
                    proc_id = self.pool.get('mrp.procurement').create(cr, uid, {
                        'name': line.name,
                        'origin': order.name,
                        'date_planned': date_planned,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_uom_qty,
                        'product_uom': line.product_uom.id,
                        'location_id': order.shop_id.warehouse_id.lot_stock_id.id,
                        'procure_method': line.type,
                        'property_ids': [(6, 0, [x.id for x in line.property_ids])],
                    })
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(uid, 'mrp.procurement', proc_id, 'button_confirm', cr)
                    self.pool.get('sale.order.line').write(cr, uid, [line.id], {'procurement_id': proc_id})
                else:
                    #
                    # No procurement because no product in the sale.order.line.
                    #
                    pass

            val = {}
            if picking_id:
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
                #val = {'picking_ids':[(6,0,[picking_id])]}  # Linea originalmente comentada. 

            if order.state=='shipping_except':
                val['state'] = 'progress'
                if (order.order_policy == 'manual') and order.invoice_ids:
                    val['state'] = 'manual'
            self.write(cr, uid, [order.id], val)
        return True
sale_order()

class sale_order_line(osv.osv):
    def _picked_sum(self, cr, uid, ids, field_name, arg, context):
        res = {}
        for sale_line in self.browse(cr, uid, ids):
            qty_sum = 0
            for picking_line in sale_line.move_ids:
                qty_sum += picking_line.product_qty
            res[sale_line.id] = qty_sum
        return res
    _inherit = "sale.order.line"
    _columns = {    
        'picked_sum': fields.function(_picked_sum, method=True, type='integer', string='Picked qty'),
        'delivery_date':fields.date('Delivery Date', select=1)
               }
sale_order_line()

   
class stock_picking(osv.osv):
    _inherit = "stock.picking"

    def unlink(self, cr, uid, ids):
        line_ids = []
        fields=['move_lines']       
        for picking in self.read(cr, uid, ids, fields, context={}):
            line_ids += picking['move_lines']
        self.pool.get('stock.move').unlink(cr, uid, line_ids)
        return super(stock_picking, self).unlink(cr, uid, ids)    
stock_picking()
                              
class stock_move(osv.osv):
    _inherit = "stock.move"
    _columns = {    
        'picking_id': fields.many2one('stock.picking', 'Packing list', select=True, ondelete='cascade'), # ondelete='cascade' added
               }  
    def unlink(self, cr, uid, ids):
        print "Dentro de Unlink de lineas"        # Pendiente de modificar el estado de las sale order line
        return super(stock_move, self).unlink(cr, uid, ids)       
stock_move()






