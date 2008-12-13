#-*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                    Pedro Tarrafeta <pedro@acysos.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from osv import fields,osv


class stock_location(osv.osv):
    _name = "stock.location"
    _description = "Location"
    _inherit = 'stock.location'    

    def _product_get_all_report(self, cr, uid, ids, product_ids=False, context={}, date_ref=False):
        return self._product_get_report(cr, uid, ids, product_ids=product_ids, context=context, date_ref=date_ref, recursive=True)

    def _product_get_report(self, cr, uid, ids, product_ids=False, context=None, date_ref=False, recursive=False):
        if context is None:
            context = {}
        product_obj = self.pool.get('product.product')
        if not product_ids:
            product_ids = product_obj.search(cr, uid, [])

        products = product_obj.browse(cr, uid, product_ids, context=context)
        products_by_uom = {}
        products_by_id = {}
        for product in products:
            products_by_uom.setdefault(product.uom_id.id, [])
            products_by_uom[product.uom_id.id].append(product)
            products_by_id.setdefault(product.id, [])
            products_by_id[product.id] = product

        result = []
        for id in ids:
            for uom_id in products_by_uom.keys():
                fnc = self._product_get
                if recursive:
                    fnc = self._product_all_get
                ctx = context.copy()
                ctx['uom'] = uom_id
                qty = fnc(cr, uid, id, [x.id for x in products_by_uom[uom_id]],
                        context=ctx, date_ref=date_ref)
                for product_id in qty.keys():
                    if not qty[product_id]:
                        continue
                    product = products_by_id[product_id]
                    result.append({
                        'price': product.list_price,
                        'name': product.name,
                        'code': product.default_code, # used by lot_overview_all report!
                        'variants': product.variants or '',
                        'uom': product.uom_id.name,
                        'amount': qty[product_id],
                    })

        return result

    def _product_get_multi_location(self, cr, uid, ids, product_ids=False, date_ref=False, context={}, states=['done'], what=('in', 'out')):
        if not date_ref:
            date_ref = time.strftime('%Y-%m-%d %H:%M:%S')
        product_obj = self.pool.get('product.product')
        states_str = ','.join(map(lambda s: "'%s'" % s, states))
        if not product_ids:
            product_ids = product_obj.search(cr, uid, [])
        res = {}
        for id in product_ids:
            res[id] = 0.0
        if not ids:
            return res

        product2uom = {}
        for product in product_obj.browse(cr, uid, product_ids, context=context):
            product2uom[product.id] = product.uom_id.id
        prod_ids_str = ','.join(map(str, product_ids))
        location_ids_str = ','.join(map(str, ids))
        results = []
        results2 = []
        if 'in' in what:
            # all moves from a location out of the set to a location in the set
            cr.execute(
                'select sum(product_qty), product_id, product_uom '\
                'from stock_move '\
                'where location_id not in ('+location_ids_str+') '\
                'and location_dest_id in ('+location_ids_str+') '\
                'and product_id in ('+prod_ids_str+') '\
                'and state in ('+states_str+') and date <= \''+date_ref+'\''\
                'group by product_id,product_uom'
            )
            results = cr.fetchall()
        if 'out' in what:
            # all moves from a location in the set to a location out of the set
            cr.execute(
                'select sum(product_qty), product_id, product_uom '\
                'from stock_move '\
                'where location_id in ('+location_ids_str+') '\
                'and location_dest_id not in ('+location_ids_str+') '\
                'and product_id in ('+prod_ids_str+') '\
                'and state in ('+states_str+') and date <= \''+date_ref+'\''\
                'group by product_id,product_uom'
            )
            results2 = cr.fetchall()
        uom_obj = self.pool.get('product.uom')
        for amount, prod_id, prod_uom in results:
            amount = uom_obj._compute_qty(cr, uid, prod_uom, amount,
                    context.get('uom', False) or product2uom[prod_id])
            res[prod_id] += amount
        for amount, prod_id, prod_uom in results2:
            amount = uom_obj._compute_qty(cr, uid, prod_uom, amount,
                    context.get('uom', False) or product2uom[prod_id])
            res[prod_id] -= amount

        return res

    def _product_get(self, cr, uid, id, product_ids=False, context={}, states=['done'], date_ref=False):
                ids = id and [id] or []
                return self._product_get_multi_location(cr, uid, ids, product_ids=product_ids, date_ref=date_ref, context=context, states=states )    

    def _product_all_get(self, cr, uid, id, product_ids=False, context={}, states=['done'], date_ref=False):
        # build the list of ids of children of the location given by id
        ids = id and [id] or []
        location_ids = self.search(cr, uid, [('location_id', 'child_of', ids)])
        return self._product_get_multi_location(cr, uid, location_ids, product_ids=product_ids, date_ref=date_ref, context=context, states=states)

    def _product_virtual_get(self, cr, uid, id, product_ids=False, context={}, states=['done'], date_ref=False):
        return self._product_all_get(cr, uid, id, product_ids=product_ids, date_ref=date_ref, context=context, states=['confirmed','waiting','assigned','done'])

stock_location()


class product_product(osv.osv):
    _inherit = "product.product"

    def _get_product_available_func(states, what):
        def _product_available(self, cr, uid, ids, name, arg, context={}):
            if context.get('shop', False):
                cr.execute('select warehouse_id from sale_shop where id=%d', (int(context['shop']),))
                res2 = cr.fetchone()
                if res2:
                    context['warehouse'] = res2[0]

            if context.get('warehouse', False):
                cr.execute('select lot_stock_id from stock_warehouse where id=%d', (int(context['warehouse']),))
                res2 = cr.fetchone()
                if res2:
                    context['location'] = res2[0]

            if context.get('location', False):
                location_ids = [context['location']]
            else:
                #cr.execute('select lot_stock_id from stock_warehouse where id=%d', (int(context['warehouse']),))
                cr.execute("select lot_stock_id from stock_warehouse")
                #cr.execute("select id from stock_location where active = true and usage = 'internal'")
                location_ids = [id for (id,) in cr.fetchall()]
            # build the list of ids of children of the location given by id
            location_ids = self.pool.get('stock.location').search(cr, uid, [('location_id', 'child_of', location_ids)])
            fecha=time.strftime('%Y-%m-%d %H:%M:%S')
            res = self.pool.get('stock.location')._product_get_multi_location(cr, uid, location_ids, ids, fecha, context, states, what)
            for id in ids:
                res.setdefault(id, 0.0)
            return res
        return _product_available
    _product_qty_available = _get_product_available_func(('done',), ('in', 'out'))
    _product_virtual_available = _get_product_available_func(('confirmed','waiting','assigned','done'), ('in', 'out'))
    _product_outgoing_qty = _get_product_available_func(('confirmed','waiting','assigned'), ('out',))
    _product_incoming_qty = _get_product_available_func(('confirmed','waiting','assigned'), ('in',))
    _columns = {
        'qty_available': fields.function(_product_qty_available, method=True, type='float', string='Real Stock'),
        'virtual_available': fields.function(_product_virtual_available, method=True, type='float', string='Virtual Stock'),
        'incoming_qty': fields.function(_product_incoming_qty, method=True, type='float', string='Incoming'),
        'outgoing_qty': fields.function(_product_outgoing_qty, method=True, type='float', string='Outgoing'),
    }
product_product()

