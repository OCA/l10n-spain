##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
#
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
import netsvc
from osv import fields, osv
# import ir
from mx import DateTime
import types


class pos_order_line(osv.osv):
	_name = "pos.order.line"
	_description = "Lines of Point of Sale"

	def onchange_ean13(self, cr, uid, ids, ean13, pricelist, qty=0, partner_id=False):

		if not ean13:
			return {'value': {} }

		obj = self.pool.get('product.product')
		ids = obj.search(cr, uid, [('ean13','=',ean13)])
		if ids:
			res = obj.read(cr, uid, ids, ['id'])
			product_id = res[0]['id']
			val = self.onchange_product_id(cr, uid, ids, pricelist, product_id, qty, partner_id)
			val['value']['product_id'] = product_id
			print val
			return val
		else :
			raise osv.except_osv('No product found !', "There isn't any product with this EAN13 code.")
			return {'value': {} }


	_inherit = 'pos.order.line'
	_columns = {
		'ean13': fields.char('EAN13', size=13),
	}
pos_order_line()
