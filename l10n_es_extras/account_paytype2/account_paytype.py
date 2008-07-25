# -*- encoding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
# Copyright (c) 2008 Pablo Rocandio (salbet@gmail.com) All Rights Reserved.
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
from osv import fields, osv

class account_paytype(osv.osv):
	_name='account.paytype'
	_description='Tipos de pago'
	_columns = {
		'name': fields.char('Tipo de Pago', size=32, translate=True, select=True),
		'active': fields.boolean('Activo', select=True),
		'link_bank': fields.boolean('Cuenta bancaria asociada', select=True),
		'note': fields.text('Descripción', translate=True, help="Descripción del tipo de pago que aparacerá en la facturas"),
	}
	_defaults = {
		'active': lambda *a: 1,
	}
	_order = "name"
account_paytype()


class res_partner(osv.osv):
	_inherit='res.partner'
	_columns={
		'tipopago_id': fields.many2one('account.paytype', 'Tipo de pago')
	}
res_partner()

# readylan *** aquí extiendo la funcionalidad a pedidos de venta
class sale_order(osv.osv):
	_inherit='sale.order'
	_columns={
		'tipopago_id': fields.many2one('account.paytype', 'Tipo de Pago'),	
		'acc_number': fields.many2one('res.partner.bank','Account number', select=True,),	
	}
	
	def onchange_partner_id2(self, cr, uid, ids, part):
    	# Copia los datos del partner en el pedido, incluyendo el nuevo campo tipopago_id
		result = self.onchange_partner_id(cr, uid, ids, part)
		tipopago_id = False
		if part:
			partner_line = self.pool.get('res.partner').browse(cr, uid, part)
			if partner_line:
				tipopago_id = partner_line.tipopago_id.id
			if tipopago_id:	
				result['value']['tipopago_id'] = tipopago_id
		return self.onchange_tipopago_id(cr, uid, ids, tipopago_id, part, result)

	def onchange_tipopago_id(self, cr, uid, ids, tipopago_id, partner_id, result = {'value': {}}):
		if tipopago_id and partner_id: 
			if self.pool.get('account.paytype').browse(cr, uid, [tipopago_id])[0].link_bank: # Si la forma de pago está asociada a una cuenta bancaria
				partner_bank_obj = self.pool.get('res.partner.bank')
				args = [('partner_id', '=', partner_id), ('default_bank', '=', 1)]
				bank_account_id = partner_bank_obj.search(cr, uid, args)
				if bank_account_id:
					#result['value']['acc_number'] = partner_bank_obj.read(cr, uid, bank_account_id[0], ['acc_number'])['acc_number']
					result['value']['acc_number'] = bank_account_id[0]
					return result
		result['value']['acc_number'] = False
		return result
		
	# readylan *** la factura generada debe recoger el tipo de pago y la cuenta bancaria del pedido de venta.
	# La funcion _make_invoice del modulo sale parece la encargada de crear la factura basándose en el pedido
	# de venta. 
	"""
	def _make_invoice(self, cr, uid, order, lines):
	"""
	
sale_order()

class account_invoice(osv.osv):
	_inherit='account.invoice'
	_columns={
		'tipopago_id': fields.many2one('account.paytype', 'Tipo de Pago'),	
		'acc_number': fields.many2one('res.partner.bank','Account number', select=True,),	
	}

	def onchange_partner_id2(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False):
		# Copia los datos del partner en la factura, incluyendo el nuevo campo tipopago_id
		result = self.onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term)
		tipopago_id = False
		if partner_id:
			partner_line = self.pool.get('res.partner').browse(cr, uid, partner_id)
			if partner_line:
				tipopago_id = partner_line.tipopago_id.id
			if tipopago_id:	
				result['value']['tipopago_id'] = tipopago_id
		return self.onchange_tipopago_id(cr, uid, ids, tipopago_id, partner_id, result)
	
	def onchange_tipopago_id(self, cr, uid, ids, tipopago_id, partner_id, result = {'value': {}}):
		if tipopago_id and partner_id: 
			if self.pool.get('account.paytype').browse(cr, uid, [tipopago_id])[0].link_bank: # Si la forma de pago está asociada a una cuenta bancaria
				partner_bank_obj = self.pool.get('res.partner.bank')
				args = [('partner_id', '=', partner_id), ('default_bank', '=', 1)]
				bank_account_id = partner_bank_obj.search(cr, uid, args)
				if bank_account_id:
					#result['value']['acc_number'] = partner_bank_obj.read(cr, uid, bank_account_id[0], ['acc_number'])['acc_number']
					result['value']['acc_number'] = bank_account_id[0]
					return result
		result['value']['acc_number'] = False
		return result

account_invoice()


class res_partner_bank(osv.osv):

	def create(self, cr, uid, vals, context=None):
		if vals['default_bank'] and vals['partner_id']:
			sql = "UPDATE res_partner_bank SET default_bank='0' WHERE partner_id=%i AND default_bank='1'" % (vals['partner_id'])
			cr.execute(sql)
		return super(res_partner_bank, self).create(cr, uid, vals, context=context)

	def write(self, cr, uid, ids, vals, context=None):
		if vals['default_bank'] == True:
			partner_id = self.pool.get('res.partner.bank').browse(cr, uid, ids)[0].partner_id.id
			sql = "UPDATE res_partner_bank SET default_bank='0' WHERE partner_id=%i AND default_bank='1' AND id<>%i" % (partner_id, ids[0])
			cr.execute(sql)
		return super(res_partner_bank, self).write(cr, uid, ids, vals, context=context)

	def name_get(self, cr, uid, ids, context=None):
		if not ids:
			return []
		bank_type_obj = self.pool.get('res.partner.bank.type')

		type_ids = bank_type_obj.search(cr, uid, [])
		bank_type_names = {}
		for bank_type in bank_type_obj.browse(cr, uid, type_ids,
				context=context):
			bank_type_names[bank_type.code] = bank_type.name

		return [(r['id'],  r['acc_number']) \
					for r in self.read(cr, uid, ids,
					[self._rec_name, 'acc_number'], context,
					load='_classic_write')]
		
	_inherit="res.partner.bank"
	_columns = {
		'default_bank' : fields.boolean('Default'),
			}

res_partner_bank()
