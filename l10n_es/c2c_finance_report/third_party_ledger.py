##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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

import pooler
import time
import re
import rml_parse
import datetime
from report import report_sxw

class third_party_ledgerc2c(rml_parse.rml_parse):
	def __init__(self, cr, uid, name, context):
		self.date_lst = []
		self.date_lst_string = ''
		super(third_party_ledgerc2c, self).__init__(cr, uid, name, context)
		self.localcontext.update( {
			'time': time,
			'lines': self.lines,
			'sum_debit_partner': self._sum_debit_partner,
			'sum_credit_partner': self._sum_credit_partner,
			'sum_debit': self._sum_debit,
			'sum_credit': self._sum_credit,
			'get_company': self._get_company,
			'get_currency': self._get_currency,
			'comma_me' : self.comma_me,
		})
	def date_range(self,start,end):
		start = datetime.date.fromtimestamp(time.mktime(time.strptime(start,"%Y-%m-%d")))
		end = datetime.date.fromtimestamp(time.mktime(time.strptime(end,"%Y-%m-%d")))
		full_str_date = []
	#
		r = (end+datetime.timedelta(days=1)-start).days
	#
		date_array = [start+datetime.timedelta(days=i) for i in range(r)]
		for date in date_array:
			full_str_date.append(str(date))
		return full_str_date
		
	#
	def transform_period_into_date_array(self,data):
		## Get All Period Date
		if not data['form']['periods'][0][2] :
			periods_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
		else:
			periods_id = data['form']['periods'][0][2]
		date_array = [] 
		for period_id in periods_id:
			period_obj = self.pool.get('account.period').browse(self.cr, self.uid, period_id)
			date_array = date_array + self.date_range(period_obj.date_start,period_obj.date_stop)
			
		self.date_lst = date_array
		self.date_lst.sort()
		
			
	def transform_date_into_date_array(self,data):
		return_array = self.date_range(data['form']['date1'],data['form']['date2'])
		self.date_lst = return_array
		self.date_lst.sort()
		
	def get_previous_unclosed_period(self,period_ids):
		## Get all periode for dates
		unclosed_fiscal_year_id =  self.pool.get('account.fiscalyear').search(self.cr, self.uid, [('state','<>','closed')])
		unclosed_period_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','in',unclosed_fiscal_year_id)])
		unclosed_period_ids = ','.join(map(str,unclosed_period_id))
		periods_ids = ','.join(map(str,period_ids))
		
		self.cr.execute("Select unper.id from account_period as unper where unper.date_start < (Select min(date_start) from account_period where id in ("+ periods_ids +") and unper.id in (" + unclosed_period_ids + "));")
		self.unclosed_period_id = ','.join([str(a) for (a,) in self.cr.fetchall()])
		
	def comma_me(self,amount):
		if  type(amount) is float :
			amount = str('%.2f'%amount)
		else :
			amount = str(amount)
		if (amount == '0'):
		     return ' '
		orig = amount
		new = re.sub("^(-?\d+)(\d{3})", "\g<1>'\g<2>", amount)
		if orig == new:
			return new
		else:
			return self.comma_me(new)
	def special_map(self):
		string_map = ''
		for date_string in self.date_lst:
			string_map = date_string + ','
		return string_map
	
	def preprocess(self, objects, data, ids):
		## Define total for partner dict
		self.tot_partner={}
		PARTNER_REQUEST = ''
		if (data['model'] == 'res.partner'):
			## Si on imprime depuis les partenaires
			if ids:
				PARTNER_REQUEST =  "AND line.partner_id IN (" + ','.join(map(str, ids)) + ")"
		# Transformation des date
		#
		#
		if data['form'].has_key('fiscalyear'): 
			self.transform_period_into_date_array(data)
		else:
			self.transform_date_into_date_array(data)
		##
		self.date_lst_string = '\'' + '\',\''.join(map(str,self.date_lst)) + '\''
		#
		#new_ids = [id for (id,) in self.cr.fetchall()]
		if data['form']['result_selection'] == 'supplier':
			ACCOUNT_TYPE = "AND a.type='payable' "
		elif data['form']['result_selection'] == 'customer':
			ACCOUNT_TYPE = "AND a.type='receivable' "
		elif data['form']['result_selection'] == 'all':
			ACCOUNT_TYPE = "AND (a.type='receivable' OR a.type='payable') "

		self.cr.execute(
			"SELECT a.id " \
			"FROM account_account a " \
			"LEFT JOIN account_account_type t " \
				"ON (a.type=t.code) " \
			"WHERE t.partner_account=TRUE " \
				"AND a.company_id = %d " \
				" " + ACCOUNT_TYPE + " " \
				"AND a.active", (data['form']['company_id'],))
		self.account_ids = ','.join([str(a) for (a,) in self.cr.fetchall()])
		
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		partner_to_use = []
		if data['model'] != 'res.partner':
			if data['form'].has_key('fiscalyear'):
				if not data['form']['periods'][0][2] :
					periods_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
				else:
					periods_id = data['form']['periods'][0][2]
				periods_ids = ','.join(map(str,periods_id))
				self.get_previous_unclosed_period(periods_id)
				## Test Period
				#
				if self.unclosed_period_id:
					unclosed_period = "AND line.period_id IN ( " + self.unclosed_period_id + ") "
				else:
					unclosed_period = ""
				#
				##
				if data['form']['soldeinit'] :
					self.cr.execute(
						"SELECT DISTINCT line.partner_id " \
						"FROM account_move_line AS line, account_account AS account " \
						"WHERE line.partner_id IS NOT NULL " \
							"AND line.account_id = account.id " \
							" " + unclosed_period + " " \
							"OR line.period_id IN ( " + periods_ids + ") " \
							"AND line.account_id IN (" + self.account_ids + ") " \
							"AND account.company_id = %d " \
							"AND account.active " ,
						(data['form']['company_id'],))
				else:
					self.cr.execute(
						"SELECT DISTINCT line.partner_id " \
						"FROM account_move_line AS line, account_account AS account " \
						"WHERE line.partner_id IS NOT NULL " \
							"AND line.account_id = account.id " \
							"AND line.period_id IN (" + periods_ids + ") " \
							"AND line.account_id IN (" + self.account_ids + ") " \
							"AND account.company_id = %d " \
							"AND account.active " ,
						(data['form']['company_id'],))
				res = self.cr.dictfetchall()
				for res_line in res:
					if res_line['partner_id'] <> None:
						partner_to_use.append(res_line['partner_id'])
			else:
				if data['form']['soldeinit'] :
					self.cr.execute(
						"SELECT DISTINCT line.partner_id " \
						"FROM account_move_line AS line, account_account AS account " \
						"WHERE line.partner_id IS NOT NULL " \
							"AND line.account_id = account.id " \
							"AND line.date < %s " \
							"OR line.date IN (" + self.date_lst_string + ") " \
							"AND line.reconcile_id IS NULL " \
							"AND line.account_id IN (" + self.account_ids + ") " \
							"AND account.company_id = %d " \
							"AND account.active " ,
						(self.date_lst[len(self.date_lst)-1],data['form']['company_id']))
				else:
					self.cr.execute(
						"SELECT DISTINCT line.partner_id " \
						"FROM account_move_line AS line, account_account AS account " \
						"WHERE line.partner_id IS NOT NULL " \
							"AND line.account_id = account.id " \
							"AND line.date IN (" + self.date_lst_string + ") " \
							"AND line.account_id IN (" + self.account_ids + ") " \
							"AND account.company_id = %d " \
							"AND account.active ",
						(data['form']['company_id'],))
				res = self.cr.dictfetchall()
				for res_line in res:
					if res_line['partner_id'] <> None:
						partner_to_use.append(res_line['partner_id'])
			new_ids = self.pool.get('res.partner').search(self.cr, self.uid, [('id','in',partner_to_use)],order='name asc')
		else:
			if data['form'].has_key('fiscalyear'):
				if not data['form']['periods'][0][2] :
					periods_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
				else:
					periods_id = data['form']['periods'][0][2]
				periods_ids = ','.join(map(str,periods_id))
				self.get_previous_unclosed_period(periods_id)
			## Si on imprime depuis les partenaires
			if ids:
				new_ids = self.pool.get('res.partner').search(self.cr, self.uid, [('id','in',ids)],order='name asc')
			
		self.partner_ids = ','.join(map(str, new_ids))
		objects = self.pool.get('res.partner').browse(self.cr, self.uid, new_ids)
			
		super(third_party_ledgerc2c, self).preprocess(objects, data, new_ids)

	def lines(self, partner,data):
		if data['form'].has_key('fiscalyear'):
			Result = self.byperiod(partner,data)
			Result.sort(self.bySequence)
			return  Result
		else:
			self.transform_date_into_date_array(data)
			Result = self.bydate(partner,data)
			Result.sort(self.bySequence)
			return  Result

	def bydate(self,partner,data):
		self.tot_partner['tot_credit'] = 0.0
		self.tot_partner['tot_debit'] = 0.0
		self.tot_partner['tot_balance'] = 0.0
		if data['form']['reconcil'] :
			RECONCILE_TAG = " "
		else:
			RECONCILE_TAG = "AND l.reconcile_id IS NULL"
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		full_account = []
		
		if data['form']['soldeinit'] and  data['form']['reconcil'] == False:
			SOLDEINIT_TAG = " AND (l.date IN (" + self.date_lst_string + ") OR l.date < '"+self.date_lst[0] + "' )"
		else:
			SOLDEINIT_TAG = " AND l.date IN (" + self.date_lst_string + ") "
			
		if data['form']['soldeinit'] and  data['form']['reconcil']:
			self.cr.execute(
					"SELECT l.id,l.date,j.code, l.ref, l.name, l.debit, l.credit " \
					"FROM account_move_line l " \
					"LEFT JOIN account_journal j " \
						"ON (l.journal_id = j.id) " \
					"WHERE l.partner_id = %d " \
						"AND l.account_id IN (" + self.account_ids + ") " \
						"AND l.date < %s " \
					"ORDER BY l.date",
					(partner.id, self.date_lst[0]))
			res = self.cr.dictfetchall()
			sum = 0.0
			sum_debit = 0.0
			sum_credit = 0.0
			for r in res:
				sum = sum + (r['debit'] - r['credit'])
				sum_debit = sum_debit + r['debit']
				sum_credit = sum_credit + r['credit']
			if res:
				r['name'] = 'Solde Initial : ' + r['name']
				r['debit'] = sum_debit
				r['credit'] = sum_credit
				r['progress'] = sum
				self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + sum_credit
				self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + sum_debit
				self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + sum
				full_account.append(r)
			
		self.cr.execute(
				"SELECT l.id " \
				"FROM account_move_line l " \
				"LEFT JOIN account_journal j " \
					"ON (l.journal_id = j.id) " \
				"WHERE l.partner_id = %d " \
					"AND l.account_id IN (" + self.account_ids + ") " \
					" " + RECONCILE_TAG + " " \
					" " + SOLDEINIT_TAG + " " \
					"ORDER BY l.date",
					(partner.id,))
		res = self.cr.fetchall()
		## We will now search if the account is reconciles or not
		line_ids = []
		for res_line in res:
			line_ids.append(res_line[0])
		search_ids = pooler.get_pool(self.cr.dbname).get('account.move.line').search(self.cr, self.uid, [('id','in',line_ids)])
		account_move_lines = pooler.get_pool(self.cr.dbname).get('account.move.line').browse(self.cr, self.uid,search_ids)
		
		for line in account_move_lines:
			## Search invoice Reference
			#
			invoice_ids = self.pool.get('account.invoice').search(self.cr, self.uid, [('move_id','=',line.move_id.id)])
			invoice_obj = self.pool.get('account.invoice').browse(self.cr, self.uid,invoice_ids)
			if invoice_obj:
				ref = invoice_obj[0].number
			else:
				ref = line.ref
			#
			##
			r = {}
			r['id'] = line.id
			r['date'] = line.date
			r['code'] = line.journal_id.code
			r['ref'] = ref
			r['name'] = line.name
			r['credit'] = line.credit
			r['debit'] = line.debit
			r['progress'] = r['debit'] - r['credit']
			r['amount_currency'] = (line.amount_currency or 0.0)
			r['currency_code'] = (line.currency_id and line.currency_id.code or '')

			if data['form']['reconcil'] :
				self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + line.credit
				self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + line.debit
				self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + (r['debit'] - r['credit'])
				full_account.append(r)
			
			else:
				if line.reconcile_id:
					reconcile_id_list = []
					for recon in line.reconcile_id.line_id:
						reconcile_id_list.append(recon.id)
					account_reconcile_move_id = pooler.get_pool(self.cr.dbname).get('account.move.line').search(self.cr, self.uid, [('date','<=',self.date_lst[0]),('id','in',reconcile_id_list)])
					## We will check if we have a difference
					if (len(account_reconcile_move_id) == len(line.reconcile_id.line_id)):
						self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + line.credit
						self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + line.debit
						self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + (r['debit'] - r['credit'])
						full_account.append(r)
				else:
					self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + line.credit
					self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + line.debit
					self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + (r['debit'] - r['credit'])
					full_account.append(r)
		return full_account

	def byperiod(self,partner,data):
		
		self.tot_partner['tot_credit'] = 0.0
		self.tot_partner['tot_debit'] = 0.0
		self.tot_partner['tot_balance'] = 0.0		
		if not data['form']['periods'][0][2] :
			periods_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
		else:
			periods_id = data['form']['periods'][0][2]
		periods_ids = ','.join(map(str,periods_id))
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		full_account = []
		#import pdb
		#pdb.set_trace()
		if data['form']['reconcil'] :
			RECONCILE_TAG = " "
		else:
			RECONCILE_TAG = "AND l.reconcile_id IS NULL"
		if data['form']['soldeinit'] and  (data['form']['reconcil'] == False):
			if self.unclosed_period_id:
				SOLDEINIT_TAG = "AND (l.period_id IN (" + periods_ids + ") OR l.period_id IN ( " + self.unclosed_period_id + ")) "
			else:
				SOLDEINIT_TAG = "AND l.period_id IN (" + periods_ids + ") "
				
		else:
			SOLDEINIT_TAG = "AND l.period_id IN (" + periods_ids + ") " 
		if self.unclosed_period_id:
			unclosed_period = "AND line.period_id IN ( " + self.unclosed_period_id + ") "
		else:
			unclosed_period = ""
		if data['form']['soldeinit'] and  data['form']['reconcil']:
			self.cr.execute(
					"SELECT line.id,line.date,j.code, line.ref, line.name, line.debit, line.credit " \
					"FROM account_move_line line " \
					"LEFT JOIN account_journal j " \
						"ON (line.journal_id = j.id) " \
					"WHERE line.partner_id = %d " \
						"AND line.account_id IN (" + self.account_ids + ") " \
						" " + unclosed_period + " " \
					"ORDER BY line.date ",
					(partner.id,))
			res = self.cr.dictfetchall()
			sum = 0.0
			sum_debit = 0.0
			sum_credit = 0.0
			for r in res:
				sum = sum + (r['debit'] - r['credit'])
				sum_debit = sum_debit + r['debit']
				sum_credit = sum_credit + r['credit']
			if res:
				r['name'] = 'Solde Initial '
				r['ref'] = ''
				r['code'] = ''
				r['date'] = self.date_lst[0]
				r['debit'] = sum_debit
				r['credit'] = sum_credit
				r['progress'] = sum
				self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + sum_credit
				self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + sum_debit
				self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + sum
				full_account.append(r)
			
		self.cr.execute(
				"SELECT l.id " \
				"FROM account_move_line l " \
				"LEFT JOIN account_journal j " \
					"ON (l.journal_id = j.id) " \
				"WHERE l.partner_id = %d " \
					"AND l.account_id IN (" + self.account_ids + ") " \
					" " + RECONCILE_TAG + " " \
					" " + SOLDEINIT_TAG + " " \
					"ORDER BY l.date ",
					(partner.id,))
		res = self.cr.fetchall()
		## We will now search if the account is reconciles or not
		line_ids = []
		for res_line in res:
			line_ids.append(res_line[0])
		search_ids = self.pool.get('account.move.line').search(self.cr, self.uid, [('id','in',line_ids)])
		account_move_lines = self.pool.get('account.move.line').browse(self.cr, self.uid,search_ids)
		
		for line in account_move_lines:
			r = {}
			## Search invoice Reference
			#
			invoice_ids = self.pool.get('account.invoice').search(self.cr, self.uid, [('move_id','=',line.move_id.id)])
			invoice_obj = self.pool.get('account.invoice').browse(self.cr, self.uid,invoice_ids)
			if invoice_obj:
				ref = invoice_obj[0].number
			else:
				ref = line.ref
			#
			##
			r['id'] = line.id
			r['date'] = line.date
			r['code'] = line.journal_id.code
			r['ref'] = ref
			r['name'] = line.name
			r['credit'] = line.credit
			r['debit'] = line.debit
			r['progress'] = r['debit'] - r['credit']
			r['amount_currency'] = line.amount_currency
			r['currency_code'] = line.currency_id and line.currency_id.code or ''
			if data['form']['reconcil'] :
				self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + line.credit
				self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + line.debit
				self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + (r['debit'] - r['credit'])
				full_account.append(r)
			
			else:
				if line.reconcile_id:
					#import pdb
					#pdb.set_trace()
					reconcile_id_list = []
					for recon in line.reconcile_id.line_id:
						reconcile_id_list.append(recon.id)
					account_reconcile_move_id = pooler.get_pool(self.cr.dbname).get('account.move.line').search(self.cr, self.uid, [('date','<=',self.date_lst[0]),('id','in',reconcile_id_list)])
					## We will check if we have a difference
					if (len(account_reconcile_move_id) == len(line.reconcile_id.line_id)):
						self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + line.credit
						self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + line.debit
						self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + (r['debit'] - r['credit'])
						full_account.append(r)
				else:
					self.tot_partner['tot_credit'] = self.tot_partner['tot_credit'] + line.credit
					self.tot_partner['tot_debit'] = self.tot_partner['tot_debit'] + line.debit
					self.tot_partner['tot_balance'] = self.tot_partner['tot_balance'] + (r['debit'] - r['credit'])
					full_account.append(r)
		return full_account

	def bySequence(self,first, second):
		"""callback function to sort """
		if first['date'] > second['date']:
			return 1
		elif first['date'] < second['date']:
			return -1
		return 0

	def _sum_debit_partner(self, partner,data):
		return self.tot_partner['tot_debit']
		
	def _sum_credit_partner(self, partner,data):
		return self.tot_partner['tot_credit']
		
	def _sum_debit(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		result_tmp = 0.0
		if data['form']['reconcil'] :
			RECONCILE_TAG = " "
		else:
			RECONCILE_TAG = "AND reconcile_id IS NULL"
		if data['form']['soldeinit'] :
			self.cr.execute(
					"SELECT sum(debit) " \
					"FROM account_move_line " \
					"WHERE partner_id IN (" + self.partner_ids + ") " \
						"AND account_id IN (" + self.account_ids + ") " \
						"AND reconcile_id IS NULL " \
						"AND date < %s " ,
					(self.date_lst[0],))
			contemp = self.cr.fetchone()
			if contemp != None:
				result_tmp = result_tmp + (contemp[0] or 0.0)
			else:
				result_tmp = result_tmp + 0.0

		self.cr.execute(
				"SELECT sum(debit) " \
				"FROM account_move_line " \
				"WHERE partner_id IN (" + self.partner_ids + ") " \
					"AND account_id IN (" + self.account_ids + ") " \
					" " + RECONCILE_TAG + " " \
					"AND date IN (" + self.date_lst_string + ") " 
				)
			
		contemp = self.cr.fetchone()	
		if contemp != None:
			result_tmp = result_tmp + (contemp[0] or 0.0)
		else:
			result_tmp = result_tmp + 0.0
		
		return result_tmp
		
		
	def _sum_credit(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		result_tmp = 0.0
		if data['form']['reconcil'] :
			RECONCILE_TAG = " "
		else:
			RECONCILE_TAG = "AND reconcile_id IS NULL"
		if data['form']['soldeinit'] :
			self.cr.execute(
					"SELECT sum(credit) " \
					"FROM account_move_line " \
					"WHERE partner_id IN (" + self.partner_ids + ") " \
						"AND account_id IN (" + self.account_ids + ") " \
						"AND reconcile_id IS NULL " \
						"AND date < %s " ,
					(self.date_lst[0],))
			contemp = self.cr.fetchone()
			if contemp != None:
				result_tmp = contemp[0] or 0.0
			else:
				result_tmp = result_tmp + 0.0
		self.cr.execute(
				"SELECT sum(credit) " \
				"FROM account_move_line " \
				"WHERE partner_id IN (" + self.partner_ids + ") " \
					"AND account_id IN (" + self.account_ids + ") " \
					" " + RECONCILE_TAG + " " \
					"AND date IN (" + self.date_lst_string + ") " 
				)
		contemp = self.cr.fetchone()	
		if contemp != None:
			result_tmp = result_tmp + (contemp[0] or 0.0)
		else:
			result_tmp = result_tmp + 0.0
		
		return result_tmp

	def _get_company(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).name

	def _get_currency(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.name
	
report_sxw.report_sxw('report.account.third_party_ledgerc2c', 'res.partner',
		'addons/c2c_finance_report/third_party_ledger.rml',parser=third_party_ledgerc2c,
		header=False)

