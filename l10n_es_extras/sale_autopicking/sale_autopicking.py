# -*- encoding: utf-8 -*-

##############################################################################
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

import netsvc
import pooler
from osv import fields, osv
from report import report_sxw


# modificamos modulo stock estableciendo autopicking a True por defecto.
class stock_picking(osv.osv):
	_inherit='stock.picking'	
	_name = "stock.picking"
	_defaults = {
		'auto_picking': lambda *a: 1,
	}

stock_picking()

class sale_order(osv.osv):
	_inherit = 'sale.order'
	_name = "sale.order"
	
	def albaranar(self, cr, uid, ids):
		# obtener el picking del pedido actual:
		pick = self.browse(cr, uid, ids)[0].picking_ids[0]
		pick.force_assign(cr, uid, [pick.id])
		# lanzar report albaran valorado
sale_order()
