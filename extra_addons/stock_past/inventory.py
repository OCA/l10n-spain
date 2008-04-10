import time
from osv import fields,osv

class stock_inventory(osv.osv):
        _name = "stock.inventory"
        _inherit = 'stock.inventory'
        
	def action_done(self, cr, uid, ids, *args):
                for inv in self.browse(cr,uid,ids):
                        move_ids = []
                        move_line=[]
                        for line in inv.inventory_line_id:
                                pid=line.product_id.id
                                price=line.product_id.standard_price or 0.0
                                amount=self.pool.get('stock.location')._product_get(cr, uid, line.location_id.id, [pid], {'uom': line.product_uom.id}, date_ref=inv.date)[pid]
                                change=line.product_qty-amount
                                if change:
                                        location_id = line.product_id.product_tmpl_id.property_stock_inventory.id
                                        value = {
                                                'name': 'INV:'+str(line.inventory_id.id)+':'+line.inventory_id.name,
                                                'product_id': line.product_id.id,
                                                'product_uom': line.product_uom.id,
                                                'date': inv.date,
                                                'date_planned': inv.date,
                                                'state': 'assigned'
                                        }
                                        if change>0:
                                                value.update( {
                                                        'product_qty': change,
                                                        'location_id': location_id,
                                                        'location_dest_id': line.location_id.id,
                                                })
                                        else:
                                                value.update( {
                                                        'product_qty': -change,
                                                        'location_id': line.location_id.id,
                                                        'location_dest_id': location_id,
                                                })
                                        move_ids.append(self.pool.get('stock.move').create(cr, uid, value))
                        if len(move_ids):
                                self.pool.get('stock.move').action_done(cr, uid, move_ids)
                        self.write(cr, uid, [inv.id], {'state':'done', 'date_done': time.strftime('%Y-%m-%d %H:%M:%S'), 'move_ids': [(6,0,move_ids)]})
                return True

stock_inventory()


class stock_inventory_line(osv.osv):
        _name = "stock.inventory.line"
        _inherit = 'stock.inventory.line'
        
	def on_change_product_id(self, cr, uid, ids, location_id, product, date_inv, uom=False):
                if not product:
                        return {}
                if not uom:
                        prod = self.pool.get('product.product').browse(cr, uid, [product], {'uom': uom})[0]
                        uom = prod.uom_id.id
                amount=self.pool.get('stock.location')._product_get(cr, uid, location_id, [product], {'uom': uom}, date_ref=date_inv)[product]
                result = {'product_qty':amount, 'product_uom':uom}
                return {'value':result}
stock_inventory_line()
