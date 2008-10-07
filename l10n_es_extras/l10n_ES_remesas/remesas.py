# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 ACYSOS S.L.. (http://acysos.com) All Rights Reserved.
#	Pedro Tarrafeta <pedro@acysos.com>
#
# Corregido para instalación TinyERP estándar 4.2.0: Zikzakmedia S.L. 2008
#   Jordi Esteve <jesteve@zikzakmedia.com>
#
# Añadidas cuentas de remesas y tipos de pago. 2008
#	Pablo Rocandio <salbet@gmail.com>
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
logger = netsvc.Logger()
from osv import osv, fields, orm
import ir
import time
import base64

import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime

import pooler


class remesas_cuenta(osv.osv):
	_name = 'remesas.cuenta'
	_description = 'Cuentas de remesas'

	def _get_cif(self, cr, uid, ids, field_name, arg, context):
		res = {}
		for line in self.browse(cr, uid, ids):
			if line.partner_id:
				res[line.id] = line.partner_id.vat
			else:
				res[line.id] = ""	
		return res
	
	def onchange_partner(self, cr, uid, ids, partner_id):
		if partner_id:		
			pool = pooler.get_pool(cr.dbname)
			obj = pool.get('res.partner')
			field = ['name']
			ids = [partner_id]
			filas = obj.read(cr, uid, ids, field) 
			return {'value':{'nombre': filas[0]["name"][:40]}}
		return {'value':{'nombre': ""}}
		
	_columns = {
		'name': fields.char('Nombre de la cuenta', size=64, select=True, required=True),
		'banco_id': fields.many2one('res.partner.bank','Cuenta bancaria', change_default=True, select=True, required=True),	
		'tipo': fields.selection([('csb_19','CSB 19'),('csb_58','CSB 58')], 'Tipo de remesa', size=6, select=True, required=True),
		'sufijo': fields.char('Sufijo',size=3, select=True, required=True),
		'remesas': fields.one2many('remesas.remesa', 'banco', 'Remesas'),
		'partner_id': fields.many2one('res.partner', 'Partner', select=True, required=True),
		'nombre': fields.char('Nombre Empresa para fichero', size=40, required=True),
		'cif': fields.function(_get_cif, method=True, string='CIF', type="char", select=True),
		}
remesas_cuenta()


class remesas_remesa(osv.osv):

	def _total(self, cr, uid, ids, prop, unknow_none,unknow_dict):
		id_set=",".join(map(str,ids))
		cr.execute("SELECT s.id,COALESCE(SUM(l.debit - l.credit),0) AS amount FROM remesas_remesa s LEFT OUTER JOIN account_move_line l ON (s.id=l.remesa_id) WHERE s.id IN ("+id_set+") GROUP BY s.id ")
		res=dict(cr.fetchall())
		return res
	
	def _get_period(self, cr, uid, data, context={}):
		pool = pooler.get_pool(cr.dbname)
		ids = pool.get('account.period').find(cr, uid, context=context)
		period_id = False
		if len(ids):
			period_id = ids[0]
		return {'period_id': period_id}
	
	_name='remesas.remesa'
	_description='Remesas'
	_order = "name desc"
	_columns={ 
		'name': fields.char('Codigo de remesa', size=15),
		'cuenta_id': fields.many2one('remesas.cuenta','Cuenta de remesas', required=True, ),
		'total': fields.function(_total, method=True, string='Importe Total' ),
		'fecha': fields.date('Fecha'),
		'fecha_cargo': fields.date('Fecha Cargo (C19)'),
		'diario': fields.many2one('account.journal', 'Diario asiento cobro'),
		'account_id': fields.many2one('account.account', 'Cuenta asiento bancario', domain=[('type','<>','view'), ('type', '<>', 'closed')]),
		'receipts': fields.one2many('account.move.line', 'remesa_id' ,'Recibos', readonly=True, states={'draft':[('readonly',False)]}),
		'texto': fields.text('Texto para el banco'),
		'state': fields.selection( (('draft','Borrador'),('confirmed','Confirmada'),('2reconcile','A Conciliar'),('done','Realizada')), 'Estado', readonly=True),
		'agrupar_recibos': fields.boolean('Agrupar Recibos'),
		'asiento': fields.many2one('account.move', 'Asiento de Cobro', readonly=True),
		'fichero': fields.binary('Fichero para el banco', readonly=True),
	}

	_defaults={
		'fecha': lambda *a: time.strftime('%Y-%m-%d'),
		'fecha_cargo': lambda *a: time.strftime('%Y-%m-%d'),
		'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'remesas.sequence'),
		'state': lambda *a: 'draft'
	}

	def reset_efectos(self, cr, uid, ids):
		id_set=",".join(map(str,ids))
		logger.notifyChannel('ids', netsvc.LOG_INFO, str(id_set))

		for remesa in self.browse(cr,uid,ids,context={}):
			cr.execute("SELECT r.id FROM account_move_line r WHERE r.remesa_id = " + str(remesa.id))
			res=cr.fetchall()
			logger.notifyChannel('res', netsvc.LOG_INFO, res)
			for recibo in res:
				logger.notifyChannel('recibo', netsvc.LOG_INFO, recibo[0])
				logger.notifyChannel('remesa.recibo', netsvc.LOG_INFO, [6, 0, [x.id for x in remesa.receipts]][2])
#				logger.notifyChannel('remesas', netsvc.LOG_INFO, recibo[0])
		return True
	
	def add_receipts(self,cr,uid,id):
		pass
	
	def remove_receipt(self):
		pass
	
	def receipt_move(self):
		pass
	
	def remesa_move(self):
		pass
	
	def button_confirm(self, cr, uid, ids, context={}):
#		self.reset_efectos(cr,uid,ids)
		self._total
#		logger.notifyChannel('remesas', netsvc.LOG_INFO, 'Presionado botón Crear')
		tipo = self.browse(cr,uid,ids)[0].cuenta_id.tipo

		if tipo=='csb_19':	
#			logger.notifyChannel('remesas',netsvc.LOG_INFO, 'Tipo: csb_19')
			self.create_csb19(cr,uid,ids)
		elif tipo=='csb_58':
#			logger.notifyChannel('remesas',netsvc.LOG_INFO, 'Tipo: csb_58')
			self.create_csb58(cr,uid,ids)
		else:
#			logger.notifyChannel('remesas',netsvc.LOG_INFO, 'Tipo: ninguno')
			pass
		self.write(cr, uid, ids, {'state':'confirmed'})
		return True
		
	def button_cancel(self, cr, uid, ids, context={}):
		self.write(cr, uid, ids, {'state':'draft'})
		return True

	def button_contabilizar(self, cr, uid, ids, context={}):
		# Inicialización del objeto....
		rem = self.browse(cr,uid,ids)
		# Recuperamos algunos parámetros como el diario y el número de asiento asociado ¿Dejarlo al final?
		journal_id = rem[0]['diario'].id
		if not journal_id:
			raise osv.except_osv('Error del usuario', 'No se ha definido en la remesa el diario para el asiento del cobro.')
		journal = self.pool.get('account.journal').browse(cr,uid, journal_id)
		if journal.sequence_id:
			name = self.pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)
		else:
			raise osv.except_osv('¡Asiento sin número !', '¡No se ha encontrado un numerador para esta secuencia!')
		
		# Inicialización de cuenta destino (de la cuenta bancaria), totalizador de importe y lineas de abono
#		logger.notifyChannel('remesas',netsvc.LOG_INFO, rem[0]['receipts'])
		dst_account_id = rem[0].account_id.id
		if not dst_account_id:
			raise osv.except_osv('Error del usuario', 'No se ha definido la cuenta contable del ingreso bancario para poder realizar el asiento del cobro.')
		importe_total = 0
		lines = []
		asientos_ids = ''
		# Iteramos por los distintos recibos asociados a la remesa...
		for recibo in rem[0]['receipts']:
			# Elegimos cuenta destino, segun cuenta asociada a recibo
			src_account_id = recibo.account_id.id
			
#			types = {'out_invoice': -1, 'in_invoice': 1, 'out_refund': 1, 'in_refund': -1}
			# Copiado de _pay_and_reconcile, del invoice.py
			direction = -1
			l1 = {
				'name': name,
				'debit': direction == 1 and (recibo.debit - recibo.credit),
				'credit': direction == -1 and (recibo.debit - recibo.credit),
				'account_id': src_account_id,
				'partner_id': recibo.partner_id['id'],
				'date': rem[0]['fecha_cargo'],
				'ref': recibo.ref,
			}
			
			importe_total += (recibo.debit - recibo.credit)
			lines.append((0,0,l1))
			asientos_ids += str(recibo.move_id.id) + ','
#			logger.notifyChannel('asientos',netsvc.LOG_INFO, asientos_ids)

		asientos_ids = asientos_ids.rstrip(',')	
		l2 = {
			'name':name,
			'debit': direction == -1 and importe_total,
			'credit': direction == 1 and importe_total,
			'account_id': dst_account_id,
			'partner_id': rem[0]['cuenta_id'].partner_id.id, # PRC
			#'partner_id': rem[0]['banco'].partner_id.id, 
			'date': rem[0]['fecha_cargo'],
		}
		lines.append((0, 0, l2))
			
#		logger.notifyChannel('lines',netsvc.LOG_INFO, lines)
			
		move = {'name': name, 'line_id': lines, 'journal_id':journal_id}
#		logger.notifyChannel('moves',netsvc.LOG_INFO, move)
			
		move_id = self.pool.get('account.move').create(cr, uid, move)
#		logger.notifyChannel('remesas',netsvc.LOG_INFO, recibo.id)
		self.write(cr,uid,ids, {'state':'2reconcile', 'asiento': move_id})
		return True


	def button_reconcile(self, cr, uid, ids, context={}):
		rem = self.browse(cr,uid,ids)
		move_id = rem[0]['asiento'].id
#		line_ids = []
#		asientos_ids = ''
#		src_account_ids = []
#		Para cada recibo de la remesa, localizamos el apunte del pago y conciliamos. Si no encontramos el pago, avisamos.
		line = self.pool.get('account.move.line')
		
		for recibo in rem[0]['receipts']:
			cr.execute('select id from account_move_line where move_id = '+str(move_id)+' and partner_id ='+str(recibo.partner_id.id)+' and ref= \''+str(recibo.ref)+'\' and debit = '+str(recibo.credit)+' and credit = '+str(recibo.debit)+' and state <> \''+str('reconciled')+'\' limit 1')
			lines = line.browse(cr, uid, map(lambda x: x[0], cr.fetchall()) )
			assert len(lines) == 1, "Error en el numero de recibos"
#			logger.notifyChannel('lines.id',netsvc.LOG_INFO, lines[0].id)
#			logger.notifyChannel('recibo.id',netsvc.LOG_INFO, recibo.id)
			self.pool.get('account.move.line').reconcile(cr, uid, [lines[0].id, recibo.id], 'remesa', 290, self._get_period(cr,uid,ids,context)['period_id'], 1, context)

#			asientos_ids += str(recibo.move_id.id) + ','
#			if recibo.account_id.id not in src_account_ids:
#				src_account_ids.append(recibo.account_id.id)
#		asientos_ids = asientos_ids.rstrip(',')	
#		logger.notifyChannel('sql',netsvc.LOG_INFO, 'in '+str(move_id) + str(asientos_ids) )
#		for l in lines:
#			if l.account_id.id==src_account_id:
#				logger.notifyChannel('cuentas', netsvc.LOG_INFO, str(l.account_id.id) + '   ' +str(src_account_id) )
#				line_ids.append(l.id)
#			logger.notifyChannel('lineas',netsvc.LOG_INFO, line_ids)
			
		self.write(cr,uid,ids, {'state':'done'})
			
		return True


	def digitos_cc(self, cc_in):
		"Quita los espacios en blanco del número de C.C. (por ej. los que pone el módulo digito_control_es)"
		cc = ""
		for i in cc_in:
			try:
				int(i)
				cc += i
			except ValueError:
				pass
		return cc


	def conv_ascii(self, text):
		"Convierte vocales accentuadas, ñ y ç a sus caracteres equivalentes ASCII"
		old_chars = ['á','é','í','ó','ú','à','è','ì','ò','ù','ä','ë','ï','ö','ü','â','ê','î','ô','û','Á','É','Í','Ú','Ó','À','È','Ì','Ò','Ù','Ä','Ë','Ï','Ö','Ü','Â','Ê','Î','Ô','Û','ñ','Ñ','ç','Ç']
		new_chars = ['a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','a','e','i','o','u','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','A','E','I','O','U','n','N','c','C']
		for old, new in zip(old_chars, new_chars):
			text = text.replace(old, new)
		return text


	def create_csb19(self,cr,uid,ids):
		txt_remesa = ''
		rem = self.browse(cr,uid,ids)[0]
		
		# Comprobamos que exista número de C.C. y que tenga 20 dígitos
		if not rem.cuenta_id: 
			raise osv.except_osv('Error del usuario', 'El C.C. de la compañía %s no existe.' % rem.cuenta_id.nombre)
					
		cc = self.digitos_cc(rem.cuenta_id.banco_id.acc_number)
		if len(cc) != 20:
			raise osv.except_osv('Error del usuario', 'El número de C.C. de la compañía %s no tiene 20 dígitos.' % rem.cuenta_id.partner_id.name)
#		logger.notifyChannel('remesas',netsvc.LOG_INFO, str(rem))

		def _cabecera_presentador_19(self,texto):
			texto += '5180'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			date_now = now().strftime('%d%m%y')
			texto += date_now
			texto += 6*' '
			texto += rem.cuenta_id.nombre.ljust(40)
			texto += 20*' '
			texto += cc[0:8]
			texto += 66*' '
			texto += '\r\n'
#			logger.notifyChannel('cabecera presentador',netsvc.LOG_INFO, texto)
			return texto

		def _cabecera_ordenante_19(self,texto):
			
			texto += '5380'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			date_now = now().strftime('%d%m%y')
			texto += date_now
			date_cargo = mx.DateTime.strptime(rem.fecha_cargo,'%Y-%m-%d')
			texto += str(date_cargo.strftime('%d%m%y'))
			texto += rem.cuenta_id.nombre.ljust(40)
			texto += cc[0:20]
			texto += 8*' '
			texto += '01'
			texto += 64*' '
 			texto += '\r\n'
			return texto

		def _individual_obligatorio_19(self,texto,recibo):
			# Comprobamos que exista número de C.C. y que tenga 20 dígitos
			if type(recibo['banco']) != str:
				raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no existe.' % recibo['nombre'])
			ccc = self.digitos_cc(recibo['banco'])
			if len(ccc) != 20:
				raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no tiene 20 dígitos.' % recibo['nombre'])

			texto += '5680'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += recibo['ref'].__str__().zfill(12)
			nombre = self.conv_ascii(recibo['nombre']).decode('ascii', 'ignore')
			texto += nombre[0:40].ljust(40)
			texto += ccc.__str__()[0:20].zfill(20)
			importe = int(round(recibo['importe']*100,0))
			texto += importe.__str__().zfill(10)
			texto += 16*' '
			texto += self.conv_ascii(recibo['concepto']).decode('ascii', 'ignore')[0:48].ljust(48)
			# Esto es lo convencional, descripción de 40 caracteres, pero se puede aprovechar los 8 espacios en blanco finales
			#texto += self.conv_ascii(recibo['concepto']).decode('ascii', 'ignore')[0:40].ljust(40)
			#texto += 8*' '
			texto += '\r\n'
			logger.notifyChannel('Individual obligatorio',netsvc.LOG_INFO, texto)
			return texto

		def _total_ordenante_19(self,texto):
			texto += '5880'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += 72*' '
			totalordenante = int(round(rem.total * 100,0))
			texto += totalordenante.__str__().zfill(10)
			texto += 6*' '
			ndomic = recibos.__len__()
#			logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
			texto += ndomic.__str__().zfill(10)
			texto += (ndomic + 2).__str__().zfill(10)
			texto += 38*' '
			texto += '\r\n'
			return texto

		def _total_general_19(self,texto):
			texto += '5980'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += 52*' '
			texto += '0001'
			texto += 16*' '
			totalremesa = int(round(rem.total * 100,0))
			texto += totalremesa.__str__().zfill(10)
			texto += 6*' '
			ndomic = recibos.__len__()
#			logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
			texto += ndomic.__str__().zfill(10)
			texto += (ndomic + 4).__str__().zfill(10)
			texto += 38*' '
			texto += '\r\n'
			return texto
			texto += '\r\n'
			return texto

		txt_remesa = _cabecera_presentador_19(self,txt_remesa)
		txt_remesa = _cabecera_ordenante_19(self,txt_remesa)
		if rem.agrupar_recibos == True: 
			#Nota: En la SELECT se ha eliminado (and b.active=True) ya que no existe el campo active
			cr.execute("""	SELECT
								p.id as ref, 
								p.name as nombre, 
								b.acc_number as banco, 
								sum(l.debit) - sum(l.credit) as importe,
								'Fras: ' || min(l.ref) || ' -> ' || max(l.ref) as concepto
							FROM 
								account_move_line l 
							LEFT OUTER JOIN 
								res_partner_bank b 
							ON 
								l.acc_number=b.id 
							LEFT OUTER JOIN
								res_partner p 
							ON
								l.partner_id=p.id 
							WHERE 
								l.remesa_id=""" + str(rem.id)+ """
							GROUP BY
								p.id,
								p.name,
								b.acc_number""")
			recibos = cr.dictfetchall()

		else:
			#Nota: En la SELECT se ha eliminado (and b.active=True) ya que no existe el campo active
			cr.execute("""	SELECT
								p.id as ref, 
								p.name as nombre, 
								b.acc_number as banco, 
								l.debit as importe, 
								'Factura ' || l.ref || '. ' || l.name as concepto 
							FROM 
								account_move_line l 
							LEFT OUTER JOIN 
								res_partner_bank b 
							ON 
								l.acc_number=b.id 
							LEFT OUTER JOIN
								res_partner p 
							ON
								l.partner_id=p.id 
							WHERE 
								l.remesa_id=""" + str(rem.id))
			recibos = cr.dictfetchall()
		
#		logger.notifyChannel('Numero de recibos',netsvc.LOG_INFO, recibos.__len__())
		
		for recibo in recibos:
#			logger.notifyChannel('recibo objeto...',netsvc.LOG_INFO, recibo)
			txt_remesa = _individual_obligatorio_19(self,txt_remesa,recibo)
	
		txt_remesa = _total_ordenante_19(self,txt_remesa)
		txt_remesa = _total_general_19(self,txt_remesa)
		self.write(cr, uid, ids, {'texto':txt_remesa, 'fichero':base64.encodestring(txt_remesa)})
#		logger.notifyChannel('remesas texto',netsvc.LOG_INFO, '\r\n' + txt_remesa)


	def create_csb58(self,cr,uid,ids):
		txt_remesa = ''
		rem = self.browse(cr,uid,ids)[0]
		# Comprobamos que exista número de C.C. y que tenga 20 dígitos
		if not rem.cuenta_id:
		#if not rem.banco: # PRC
			raise osv.except_osv('Error del usuario', 'El C.C. de la compañía %s no existe.' % rem.cuenta_id.nombre)
		cc = self.digitos_cc(rem.cuenta_id.banco_id.acc_number)
		if len(cc) != 20:
			raise osv.except_osv('Error del usuario', 'El número de C.C. de la compañía %s no tiene 20 dígitos.' % rem.cuenta_id.partner_id.name)
#		logger.notifyChannel('remesas',netsvc.LOG_INFO, str(rem))

		def _cabecera_presentador_58(self,texto):
			texto += '5170'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			date_now = now().strftime('%d%m%y')
			texto += date_now
			texto += 6*' '
			texto += rem.cuenta_id.nombre.ljust(40)
			texto += 20*' '
			texto += cc[0:8]
			texto += 66*' '
			texto += '\n'
#			logger.notifyChannel('cabecera presentador',netsvc.LOG_INFO, texto)
			return texto

		def _cabecera_ordenante_58(self,texto):
			texto += '5370'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			date_now = now().strftime('%d%m%y')
			texto += date_now
			texto += 6*' '
			texto += rem.cuenta_id.nombre.ljust(40)
			texto += cc[0:20]
			texto += 8*' '
			texto += '06'
			texto += 52*' '
			# Codigo INE de la plaza... en blanco...
			texto += 9*' '
			texto += 3*' '
 			texto += '\n'
			return texto

		def _individual_obligatorio_58(self,texto,recibo):
			# Comprobamos que exista número de C.C. y que tenga 20 dígitos
			if type(recibo['banco']) != str:
				raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no existe.' % recibo['nombre'])
			ccc = self.digitos_cc(recibo['banco'])
			if len(ccc) != 20:
				raise osv.except_osv('Error del usuario', 'El número de C.C. del cliente %s no tiene 20 dígitos.' % recibo['nombre'])

			texto += '5670'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += recibo['ref'].__str__().zfill(12)
			nombre = self.conv_ascii(recibo['nombre']).decode('ascii', 'ignore')
			texto += nombre[0:40].ljust(40)
			texto += ccc.__str__()[0:20].zfill(20)
			importe = int(round(recibo['importe']*100,0))
			texto += importe.__str__().zfill(10)
			texto += 16*' '
			texto += self.conv_ascii(recibo['concepto']).__str__()[0:40].ljust(40)
			texto += recibo['vencimiento']
			texto += 2*' '
			texto += '\n'
#			logger.notifyChannel('Individual obligaotrio',netsvc.LOG_INFO, texto)
			return texto

		def _registro_obligatorio_domicilio_58(self,texto,recibo):
			texto += '5676'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += recibo['ref'].__str__().zfill(12)
			texto += self.conv_ascii(recibo['nombre']).ljust(40)
			texto += recibo['banco'].__str__()[0:20].zfill(20)
			importe = int(recibo['importe']*100)
			texto += importe.__str__().zfill(10)
			texto += 16*' '
			texto += self.conv_ascii(recibo['concepto']).__str__()[0:40].ljust(40)
			texto += recibo['vencimiento']
			texto += '  '
			texto += '\n'
#			logger.notifyChannel('Individual obligaotrio',netsvc.LOG_INFO, texto)
			return texto

		def _total_ordenante_58(self,texto):
			texto += '5870'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += 72*' '
			totalordenante = int(rem.total * 100)
			texto += totalordenante.__str__().zfill(10)
			texto += 6*' '
			ndomic = recibos.__len__()
#			logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
			texto += ndomic.__str__().zfill(10)
			texto += (ndomic + 2).__str__().zfill(10)
			texto += 38*' '
			texto += '\n'
			return texto

		def _total_general_58(self,texto):
			texto += '5970'
			texto += (rem.cuenta_id.partner_id.vat+rem.cuenta_id.sufijo).zfill(12)
			texto += 52*' '
			texto += '0001'
			texto += 16*' '
			totalremesa = int(round(rem.total * 100,0))
			texto += totalremesa.__str__().zfill(10)
			texto += 6*' '
			ndomic = recibos.__len__()
#			logger.notifyChannel('Numero de recibos tot',netsvc.LOG_INFO, ndomic.__str__())
			texto += ndomic.__str__().zfill(10)
			texto += (ndomic + 4).__str__().zfill(10)
			texto += 38*' '
			texto += '\n'
			return texto

		txt_remesa = _cabecera_presentador_58(self,txt_remesa)
		txt_remesa = _cabecera_ordenante_58(self,txt_remesa)
		if rem.agrupar_recibos == True:
			#Nota: En la SELECT se ha eliminado (and b.active=True) ya que no existe el campo active
			cr.execute("""	SELECT
								p.id as ref, 
								p.name as nombre, 
								b.acc_number as banco, 
								sum(l.debit) - sum(l.credit) as importe,
								'Fras: ' || min(l.ref) || ' -> ' || max(l.ref) as concepto,
								to_char(l.date_maturity, 'DDMMYY') as vencimiento
							FROM 
								account_move_line l 
							LEFT OUTER JOIN 
								res_partner_bank b 
							ON 
								l.acc_number=b.id 
							LEFT OUTER JOIN
								res_partner p 
							ON
								l.partner_id=p.id 
							WHERE 
								l.remesa_id=""" + str(rem.id)+ """
							GROUP BY
								p.id,
								p.name,
								b.acc_number,
								vencimiento""")
			recibos = cr.dictfetchall()
		else:
			#Nota: En la SELECT se ha eliminado (and b.active=True) ya que no existe el campo active
			cr.execute("""	SELECT
								p.id as ref, 
								p.name as nombre, 
								b.acc_number as banco, 
								l.debit as importe, 
								'Factura ' || l.ref || '. ' || l.name as concepto,
								to_char(l.date_maturity, 'DDMMYY') as vencimiento
							FROM 
								account_move_line l 
							LEFT OUTER JOIN 
								res_partner_bank b 
							ON 
								l.acc_number=b.id 
							LEFT OUTER JOIN
								res_partner p 
							ON
								l.partner_id=p.id 
							WHERE 
								l.remesa_id=""" + str(rem.id))
			recibos = cr.dictfetchall()
		
#		logger.notifyChannel('Numero de recibos',netsvc.LOG_INFO, recibos.__len__())
		
		for recibo in recibos:
#			logger.notifyChannel('recibo objeto...',netsvc.LOG_INFO, recibo)
			if not recibo['vencimiento']:
				raise osv.except_osv('Error del usuario', 'Añada la fecha de vencimiento a todos los recibos')
			txt_remesa = _individual_obligatorio_58(self,txt_remesa,recibo)
	
		txt_remesa = _total_ordenante_58(self,txt_remesa)
		txt_remesa = _total_general_58(self,txt_remesa)
		self.write(cr, uid, ids, {'texto':txt_remesa, 'fichero':base64.encodestring(txt_remesa)})
#		logger.notifyChannel('remesas texto',netsvc.LOG_INFO, '\r\n' + txt_remesa)

remesas_remesa()


class account_move_line(osv.osv):
	_name='account.move.line'
	_inherit='account.move.line'
	_table='account_move_line'

	def _tipopago_n(self, cr, uid, ids, field_name, arg, context={}):
		result = {}
		for rec in self.browse(cr, uid, ids, context):
			cr.execute("SELECT id, tipopago_id FROM account_invoice WHERE move_id = %d", (rec.move_id.id,))
			res = cr.fetchall()
#			logger.notifyChannel('Facturas...', netsvc.LOG_INFO, res)
			if res and res[0][1]:
				remesa_id = res[0][1]
				result[rec.id] = (remesa_id, self.pool.get('account.paytype').browse(cr, uid, remesa_id).name)
			else:
				result[rec.id] = (0,0)
		return result

	def write(self, cr, uid, ids, vals, context=None, check=True, update_check=True):
		for key in vals.keys():
			if key not in ['acc_number', 'cheque_recibido', 'date_maturity']:
				return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check=True)
		return super(account_move_line, self).write(cr, uid, ids, vals, context, check, update_check=False)


	_columns ={
		'remesa_id': fields.many2one('remesas.remesa','Remesa'),
		'tipopago_id': fields.function(_tipopago_n, method=True, type="many2one", relation="account.paytype", string="Tipo de Pago"),
	}

account_move_line()

class account_invoice(osv.osv):
	_inherit = "account.invoice"
	
	def action_move_create(self, cr, uid, ids, *args):
		ret = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
		if ret:
			move_line_ids = []
			for inv in self.browse(cr, uid, ids):
				for move_line in inv.move_id.line_id:
					if move_line.account_id.type == 'receivable' and move_line.state != 'reconciled' and not move_line.remesa_id.id and not move_line.reconcile_id.id:
						move_line_ids.append(move_line.id)
				if len(move_line_ids) and inv.acc_number.id:
					aml_obj = self.pool.get("account.move.line")
					aml_obj.write(cr, uid, move_line_ids, {'acc_number': inv.acc_number.id})
		return ret

account_invoice()
