# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#					Pedro Tarrafeta <pedro@acysos.com>
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
#Este módulo añade la condición 'Días de Pago' para las formas de pago. Los días
#de pago se especifican en una cadena separada por guiones. Ejemplo, una empresa 
#paga los días 5, 15 y 25 de cada mes, tendrá unos días de pago indicados por
#5-15-25
##############################################################################

import time
import netsvc
# Activar el logger para obtener información para debug
logger = netsvc.Logger()
from osv import fields, osv
import ir

from tools.misc import currency

from copy import copy

# El modulo mx.DateTime permite realizar operaciones complejas con fechas
import mx.DateTime
from mx.DateTime import RelativeDateTime, now, DateTime, localtime


class res_partner(osv.osv):
	_name='res.partner'
	_inherit='res.partner'
	_table='res_partner'
	_columns={
		'payment_days':fields.char('Días de pago', size=25),
	}

	def _check_payment_days(self,cr,uid,id,context={}):
		res = self.read(cr,uid,id,['payment_days'])
		if res[0]['payment_days'] == False:
			return True
		paydays_list= res[0]['payment_days'].split('-')
		try:
			paydays_list = map(int, paydays_list)
		except:
			return False
		paydays_list.sort()
		for payday in paydays_list:
			if payday > 0 and payday < 31:
				pass
			else:
				return False
		return True

	def on_change_paydays(self, cr, uid, ids, payment_days): 
		days = []
		day = ''
		if payment_days:
			for char in payment_days + " ":
				if char.isdigit():
					day += char
				else:
					if day:
						intday = int(day)
						if intday <= 31 and intday > 0:
					 	   if intday not in days:
								days.append(intday)
						day = ''
		days.sort()
		payment_days = '-'.join(map(str,days))
		return {'value':{'payment_days': payment_days}}

	_constraints = [(_check_payment_days, "Error: Los días de pago deben ser números separados por guiones", ['payment_days'])]


res_partner()

# Se modifica la clase de las formas de pago. El método 'compute' modificado tiene en cuenta
# la condición 'Días de Pago' y calcula las fechas de vencimiento de los efectos según esa
# condición, trás aplicar los correspondiente vencimientos. Los loggers para debug están 
# desactivados


class account_payment_term(osv.osv):
	_name="account.payment.term"
	_inherit="account.payment.term"
	
	def compute(self, cr, uid, id, value, paydays, date_ref=False, context={}):
		if not date_ref:
			date_ref = now().strftime('%Y-%m-%d')
		pt = self.browse(cr, uid, id, context)
		amount = value
		result = []
		aux_date = mx.DateTime.strptime(date_ref, '%Y-%m-%d')
#		logger.notifyChannel('aux_date',netsvc.LOG_INFO, aux_date)
		for line in pt.line_ids:
			if line.value=='fixed':
				amt = line.value_amount
			elif line.value=='procent':
				amt = round(amount * line.value_amount,2)
			elif line.value=='balance':
				amt = amount
			if amt:
				next_date = aux_date + RelativeDateTime(days=line.days)
#				logger.notifyChannel('_date',netsvc.LOG_INFO, next_date)
				if line.condition == 'end of month':
					next_date += RelativeDateTime(day=-1)
				# Esta condición es la que se añade. Se crea una lista a partir de la cadena de 'Días de Pago'
				# y se ordena. Trás aplicar los días de plazo par el efecto se recorre la lista y se calcula 
				# la fecha de vencimiento. Se ha añadido un día extra "en el mes siguiente" para vencimientos
				# posteriores a la última fecha. Dicho día es el primero de la lista del mes siguiente. Ejemplo: día 35 de 
				# noviembre = 5 de Diciembre
				if line.condition == 'payment days' and paydays:
					payment_days_list = map(int,paydays.split('-'))
#					logger.notifyChannel('Dias de pago',netsvc.LOG_INFO, payment_days_list)
					payment_days_list.sort()
#					logger.notifyChannel('Dias de pago,2',netsvc.LOG_INFO, payment_days_list)
					payment_days_list.append(next_date.days_in_month + payment_days_list[0])
#					logger.notifyChannel('Dias de pago 3',netsvc.LOG_INFO, payment_days_list)
					for pay_day in payment_days_list:
						if next_date <= next_date + RelativeDateTime(day=pay_day):
#							logger.notifyChannel('next_date1',netsvc.LOG_INFO, next_date)
#							logger.notifyChannel('next_date1',netsvc.LOG_INFO, pay_day)
							next_date = next_date + RelativeDateTime(day=pay_day)
#							logger.notifyChannel('next_date1',netsvc.LOG_INFO, next_date)
							# Se debe establecer un criterio de como actuar en el caso
							# de que en un mes no exista el día de pago. ¿Qué se hace
							# si el día de pago es el 30 y estamos en febrero?. Las 
							# tres siguiente líneas hacen que en este caso  
							# se tome como día de pago el último día del mes.
							# Si se comentan estas líneas el día de pago será el
							# día 1 o 2 del mes siguiente.
							previous_month = next_date - RelativeDateTime(months=1)
							while next_date.day not in payment_days_list + [previous_month.days_in_month]:
								next_date = next_date - RelativeDateTime(days=1)
							break
				result.append( (next_date.strftime('%Y-%m-%d'), amt) )
				amount -= amt
		return result	

account_payment_term()


# Se añade la condición Días de Pago en las lineas de las formas de Pago

class account_payment_term_line(osv.osv):
	_name = "account.payment.term.line"
	_inherit = "account.payment.term.line"
	_columns = {
		'condition': fields.selection([('net days','Net Days'),('end of month','End of Month'),('payment days','Días de pago')], 'Condition', required=True, help="El cálculo de fechas de vencimiento ser realiza de 3 maneras: dí­as netos, fin de mes o dí­as de pago. La condición 'dí­as netos' implica que el pago será tras 'Numero de dí­as' días. La opción de 'final de mes' hace que el pago sea el último día de mes tras el número de días indicado. La opción 'Días de pago' significa que el vencimiento será en los días de pago especificados en la ficha del cliente."),
	}
account_payment_term_line()

# Se modifica la clase account_invoice en su método action_move_create que es el que crea el asiento contable
# de las facturas. La modificación viene dada porque la sustitución del método 'compute' de las formas de pago
# obliga a llamar a éste con un parámetro adicional 'paydays'
class account_invoice(osv.osv):
	_name="account.invoice"
	_inherit="account.invoice"
	_columns = {
				'move_id': fields.many2one('account.move', 'Invoice Movement', readonly= True, relate=True),
	}
	
	def action_move_create(self, cr, uid, ids, *args):
		ait_obj = self.pool.get('account.invoice.tax')
		cur_obj = self.pool.get('res.currency')
		for inv in self.browse(cr, uid, ids):
			if inv.move_id:
				continue
			if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0):
				print inv.check_total,  inv.amount_total
				raise osv.except_osv('Bad total !', 'Please verify the price of the invoice !\nThe real total does not match the computed total.')
			company_currency = inv.company_id.currency_id.id
			# create the analytical lines
			line_ids = self.read(cr, uid, [inv.id], ['invoice_line'])[0]['invoice_line']
			ils = self.pool.get('account.invoice.line').read(cr, uid, line_ids)
			# one move line per invoice line
			iml = self._get_analityc_lines(cr, uid, inv.id)
			# check if taxes are all computed
			compute_taxes = ait_obj.compute(cr, uid, inv.id)
			if not inv.tax_line:
				for tax in compute_taxes.values():
					ait_obj.create(cr, uid, tax)
			else:
				tax_key = []
				for tax in inv.tax_line:
					if tax.manual:
						continue
					key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id)
					tax_key.append(key)
					if not key in compute_taxes:
						raise osv.except_osv('Warning !', 'Global taxes defined, but not in invoice lines !')
					base = compute_taxes[key]['base']
					if abs(base - tax.base) > inv.company_id.currency_id.rounding:
						raise osv.except_osv('Warning !', 'Tax base different !\nClick on compute to update tax base')
				for key in compute_taxes:
					if not key in tax_key:
						raise osv.except_osv('Warning !', 'Taxes missing !')

			# one move line per tax line
			iml += ait_obj.move_line_get(cr, uid, inv.id)

			if inv.type in ('in_invoice', 'in_refund'):
				ref = inv.reference
			else:
				ref = self._convert_ref(cr, uid, inv.number)

			diff_currency_p = inv.currency_id.id <> company_currency
			# create one move line for the total and possibly adjust the other lines amount
			total = 0
			total_currency = 0
			for i in iml:
				if inv.currency_id.id != company_currency:
					i['currency_id'] = inv.currency_id.id
					i['amount_currency'] = i['price']
					i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
							company_currency, i['price'],
							context={'date': inv.date_invoice})
				else:
					i['amount_currency'] = False
					i['currency_id'] = False
				i['ref'] = ref
				if inv.type in ('out_invoice','in_refund'):
					total += i['price']
					total_currency += i['amount_currency'] or i['price']
					i['price'] = - i['price']
				else:
					total -= i['price']
					total_currency -= i['amount_currency'] or i['price']
			acc_id = inv.account_id.id

			name = inv['name'] or '/'
			totlines = False
			if inv.payment_term:
				partner_paydays = self.pool.get('res.partner').read(cr,uid,[inv.partner_id.id],['payment_days'])
				paydays = partner_paydays[0]['payment_days']
				totlines = self.pool.get('account.payment.term').compute(cr, uid, inv.payment_term.id, total, paydays, inv.date_invoice)
				#totlines = self.pool.get('account.payment.term').compute(cr, uid, inv.payment_term.id, total, paydays, )
			if totlines:
				logger.notifyChannel('totlines', netsvc.LOG_INFO, totlines)
				res_amount_currency = total_currency
				i = 0
				for t in totlines:
					if inv.currency_id.id != company_currency:
						amount_currency = cur_obj.compute(cr, uid,
								company_currency, inv.currency_id.id, t[1])
					else:
						amount_currency = False

					# last line add the diff
					res_amount_currency -= amount_currency or 0
					i += 1
					if i == len(totlines):
						amount_currency += res_amount_currency

					iml.append({
						'type': 'dest',
						'name': name,
						'price': t[1],
						'account_id': acc_id,
						'date_maturity': t[0],
						'amount_currency': diff_currency_p \
								and  amount_currency or False,
						'currency_id': diff_currency_p \
								and inv.currency_id.id or False,
						'ref': ref,
					})
			else:
				iml.append({
					'type': 'dest',
					'name': name,
					'price': total,
					'account_id': acc_id,
					'date_maturity' : inv.date_due or False,
					'amount_currency': diff_currency_p \
							and total_currency or False,
					'currency_id': diff_currency_p \
							and inv.currency_id.id or False,
					'ref': ref
			})

			date = inv.date_invoice
			part = inv.partner_id.id
			line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part, date, context={})) ,iml)

			journal_id = inv.journal_id.id #self._get_journal(cr, uid, {'type': inv['type']})
			journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
			if journal.sequence_id:
				name = self.pool.get('ir.sequence').get_id(cr, uid, journal.sequence_id.id)

			move = {'name': name, 'line_id': line, 'journal_id': journal_id}
			if inv.period_id:
				move['period_id'] = inv.period_id.id
				for i in line:
					i[2]['period_id'] = inv.period_id.id
			move_id = self.pool.get('account.move').create(cr, uid, move)
			# make the invoice point to that move
			self.write(cr, uid, [inv.id], {'move_id': move_id})
			self.pool.get('account.move').post(cr, uid, [move_id])
		self._log_event(cr, uid, ids)
		return True
account_invoice()

class account_invoice(osv.osv):
	_name = "account.invoice"
	_inherit="account.invoice"
	_description = 'Invoice'
	def onchange_payment_term_date_invoice(self, cr, uid, ids, payment_term_id, date_invoice, partner_id):
		if not payment_term_id:
			return {}
		res={}
		if partner_id:
			partner_paydays = self.pool.get('res.partner').read(cr,uid,[partner_id],['payment_days'])
			paydays = partner_paydays[0]['payment_days']
			if not paydays:
				paydays = ''
		else:
			paydays = ''
		pt_obj= self.pool.get('account.payment.term')

		if not date_invoice :
			date_invoice = self._defaults["date_invoice"](cr,uid,{})

		pterm_list= pt_obj.compute(cr, uid, payment_term_id, value=1, paydays=paydays, date_ref=date_invoice)

		if pterm_list:
			pterm_list = [line[0] for line in pterm_list]
			pterm_list.sort()
			res= {'value':{'date_due': pterm_list[-1]}}

		return res


	def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False):
		invoice_addr_id = False
		contact_addr_id = False
		partner_payment_term = False
		acc_id = False

		opt = [('uid', str(uid))]
		if partner_id:
			opt.insert(0, ('id', partner_id))
			res = self.pool.get('res.partner').address_get(cr, uid, [partner_id], ['contact', 'invoice'])
			contact_addr_id = res['contact']
			invoice_addr_id = res['invoice']
			p = self.pool.get('res.partner').browse(cr, uid, partner_id)
			if type in ('out_invoice', 'out_refund'):
				acc_id = p.property_account_receivable.id
			else:
				acc_id = p.property_account_payable.id

			partner_payment_term = p.property_payment_term and p.property_payment_term.id or False

		result = {'value': {
			'address_contact_id': contact_addr_id,
			'address_invoice_id': invoice_addr_id,
			'account_id': acc_id,
			'payment_term': partner_payment_term}
		}
		print "payment_term", str(payment_term)
		print "partner_payment_term", str(partner_payment_term)
		if payment_term != partner_payment_term:
			if partner_payment_term:
				to_update = self.onchange_payment_term_date_invoice(
					cr,uid,ids,partner_payment_term,date_invoice, partner_id)
				print to_update
				result['value'].update(to_update['value'])
			else:
				result['value']['date_due'] = False
		return result

account_invoice()

