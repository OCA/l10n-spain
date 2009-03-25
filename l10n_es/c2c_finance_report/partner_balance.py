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
import datetime
from report import report_sxw


class partner_balancec2c(report_sxw.rml_parse):
	def __init__(self, cr, uid, name, context):
		super(partner_balancec2c, self).__init__(cr, uid, name, context)
		self.date_lst = []
		self.date_lst_string = ''
		self.localcontext.update( {
			'time': time,
			'lines': self.lines,
			'sum_debit': self._sum_debit,
			'sum_credit': self._sum_credit,
			'sum_litige': self._sum_litige,
			'sum_sdebit': self._sum_sdebit,
			'sum_scredit': self._sum_scredit,
			'solde_debit': self._solde_balance_debit,
			'solde_credit': self._solde_balance_credit,
			'get_company': self._get_company,
			'get_currency': self._get_currency,
			'comma_me' : self.comma_me,
		})
		## Compute account list one time
	#
	# Date Management
	#
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


	def get_previous_unclosed_period(self,period_ids):
		## Get all periode for dates
		unclosed_fiscal_year_id =  self.pool.get('account.fiscalyear').search(self.cr, self.uid, [('state','<>','closed')])
		unclosed_period_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','in',unclosed_fiscal_year_id)])
		unclosed_period_ids = ','.join(map(str,unclosed_period_id))
		periods_ids = ','.join(map(str,period_ids))
		
		self.cr.execute("Select unper.id from account_period as unper where unper.date_start < (Select min(date_start) from account_period where id in ("+ periods_ids +") and unper.id in (" + unclosed_period_ids + "));")
		self.unclosed_period_id = ','.join([str(a) for (a,) in self.cr.fetchall()])
		
	def transform_period_into_date_array(self,data):
		## Get All Period Date
		#
		# If we have no period we will take all perdio in the FiscalYear.
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
		
	def preprocess(self, objects, data, ids):
		# Transformation des date
		#
		#
		if data['form'].has_key('fiscalyear'): 
			self.transform_period_into_date_array(data)
		else:
			self.transform_date_into_date_array(data)
		##
		self.date_lst_string = '\'' + '\',\''.join(map(str,self.date_lst)) + '\''
		## Compute Code
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		#
		if (data['form']['result_selection'] == 'customer' ):
			self.ACCOUNT_TYPE = "('receivable')"
		elif (data['form']['result_selection'] == 'supplier'):
			self.ACCOUNT_TYPE = "('payable')"
		else:
			self.ACCOUNT_TYPE = "('payable','receivable')"
		#
		self.cr.execute('SELECT a.id ' \
				'FROM account_account a ' \
				'LEFT JOIN account_account_type t ' \
					'ON (a.type = t.code) ' \
				'WHERE t.partner_account = TRUE ' \
					'AND a.company_id = %d ' \
					'AND a.type IN ' + self.ACCOUNT_TYPE + " " \
					'AND a.active', (data['form']['company_id'],))
		self.account_ids = ','.join([str(a) for (a,) in self.cr.fetchall()])
		
		super(partner_balancec2c, self).preprocess(objects, data, ids)

	def lines(self,data):
		if data['form'].has_key('fiscalyear'): 
			if not data['form']['periods'][0][2] :
				periods_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
			else:
				periods_id = data['form']['periods'][0][2]
			self.get_previous_unclosed_period(periods_id)
			return  self.byperiod(data)
		else:
			self.transform_date_into_date_array(data)
			return self.bydate(data)
	def bydate(self,data):
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		full_account = []
		result_tmp = 0.0

		#
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
				"SELECT p.ref, p.name,l.account_id,ac.name as account_name,ac.code as code , sum(debit) as debit, sum(credit) as credit, " \
						"CASE WHEN sum(debit) > sum(credit) " \
							"THEN sum(debit) - sum(credit) " \
							"ELSE 0 " \
						"END AS sdebit, " \
						"CASE WHEN sum(debit) < sum(credit) " \
							"THEN sum(credit) - sum(debit) " \
							"ELSE 0 " \
						"END AS scredit, " \
						"(SELECT sum(amount_currency) " \
							"FROM account_move_line l " \
							"WHERE partner_id = p.id " \
								"AND (date < %s " \
								"AND blocked = TRUE ) " \
								"OR (l.date IN (" + self.date_lst_string + ") " \
								"AND blocked = TRUE ) " \
						") AS sum_currency " \
				"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) " \
				"LEFT JOIN res_currency c on (l.currency_id=c.id) " \
				"JOIN account_account ac ON (l.account_id = ac.id)" \
				"WHERE " \
					" account_id IN (" + self.account_ids + ") " \
					"AND ((l.date < %s  ) OR (l.date IN (" + self.date_lst_string + ") ))" \
				"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code " \
				"ORDER BY l.account_id,p.name",
				(self.date_lst[0],self.date_lst[0]))
			res = self.cr.dictfetchall()
			for r in res:
				full_account.append(r)
		
		#
		#
		#
		else:
			self.cr.execute(
				"SELECT p.ref,l.account_id,ac.name as account_name,ac.code as code ,p.name, sum(debit) as debit, sum(credit) as credit, " \
						"CASE WHEN sum(debit) > sum(credit) " \
							"THEN sum(debit) - sum(credit) " \
							"ELSE 0 " \
						"END AS sdebit, " \
						"CASE WHEN sum(debit) < sum(credit) " \
							"THEN sum(credit) - sum(debit) " \
							"ELSE 0 " \
						"END AS scredit, " \
						"(SELECT sum(amount_currency) " \
							"FROM account_move_line l " \
							"WHERE partner_id = p.id " \
								"AND l.date IN (" + self.date_lst_string + ") " \
								"AND blocked = TRUE " \
						") AS sum_currency " \
				"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) " \
				"LEFT JOIN res_currency c on (l.currency_id=c.id) " \
				"JOIN account_account ac ON (l.account_id = ac.id)" \
				"WHERE  " \
					" account_id IN (" + self.account_ids + ") " \
					"AND l.date IN (" + self.date_lst_string + ") " \
				"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code " \
				"ORDER BY l.account_id,p.name")
			res = self.cr.dictfetchall()
			for r in res:
				full_account.append(r)
		
		## We will now compute Total
		return self._add_subtotal(full_account)


	def byperiod(self,data):
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		full_account = []
		result_tmp = 0.0
		if not data['form']['periods'][0][2] :
			periods_id =  self.pool.get('account.period').search(self.cr, self.uid, [('fiscalyear_id','=',data['form']['fiscalyear'])])
		else:
			periods_id = data['form']['periods'][0][2]
		#
		#
		periods_ids = ','.join(map(str,periods_id))
		#
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
				"SELECT p.ref, p.name,l.account_id,ac.name as account_name,ac.code as code , sum(debit) as debit, sum(credit) as credit, " \
						"CASE WHEN sum(debit) > sum(credit) " \
							"THEN sum(debit) - sum(credit) " \
							"ELSE 0 " \
						"END AS sdebit, " \
						"CASE WHEN sum(debit) < sum(credit) " \
							"THEN sum(credit) - sum(debit) " \
							"ELSE 0 " \
						"END AS scredit, " \
						"(SELECT sum(amount_currency) " \
							"FROM account_move_line l " \
							"WHERE partner_id = p.id " \
								"AND (period_id in ("+ self.unclosed_period_id + ") " \
								"AND blocked = TRUE ) " \
								"OR (period_id in ("+ periods_ids + ") " \
								"AND blocked = TRUE ) " \
						") AS sum_currency " \
				"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) " \
				"LEFT JOIN res_currency c on (l.currency_id=c.id) " \
				"JOIN account_account ac ON (l.account_id = ac.id)" \
				"WHERE " \
					" account_id IN (" + self.account_ids + ") " \
					"AND ((period_id in ("+ self.unclosed_period_id + ") ) OR (period_id in ("+ periods_ids + "))) " \
				"GROUP BY p.id,p.ref, p.name,l.account_id,ac.name,ac.code " \
				"ORDER BY l.account_id,p.name",
				(self.date_lst[0],self.date_lst[0]))
			res = self.cr.dictfetchall()
			for r in res:
				full_account.append(r)
		#
		#
		#
		else:
			self.cr.execute(
				"SELECT p.ref,l.account_id,ac.name as account_name,ac.code as code ,p.name, sum(debit) as debit, sum(credit) as credit, " \
						"CASE WHEN sum(debit) > sum(credit) " \
							"THEN sum(debit) - sum(credit) " \
							"ELSE 0 " \
						"END AS sdebit, " \
						"CASE WHEN sum(debit) < sum(credit) " \
							"THEN sum(credit) - sum(debit) " \
							"ELSE 0 " \
						"END AS scredit, " \
						"(SELECT sum(amount_currency) " \
							"FROM account_move_line l " \
							"WHERE partner_id = p.id " \
								"AND l.period_id IN (" + periods_ids + ") " \
								"AND blocked = TRUE " \
						") AS sum_currency " \
				"FROM account_move_line l LEFT JOIN res_partner p ON (l.partner_id=p.id) " \
				"LEFT JOIN res_currency c on (l.currency_id=c.id) " \
				"JOIN account_account ac ON (l.account_id = ac.id) " \
				"WHERE  " \
					" account_id IN (" + self.account_ids + ") " \
					"AND l.period_id IN (" + periods_ids + ") " \
				"GROUP BY p.id, p.ref, p.name,l.account_id,ac.name,ac.code " \
				"ORDER BY l.account_id,p.name")
			res = self.cr.dictfetchall()
			for r in res:
				full_account.append(r)
		
		## We will now compute Total
		return self._add_subtotal(full_account)
	
		
	def bySequence(self,first, second):
		"""callback function to sort """
		if first['account_id'] < second['account_id']:
			return 1
		elif first['account_id'] > second['account_id']:
			return -1
		return 0

	def _add_subtotal(self,cleanarray):
		i=0
		
		cleanarray.sort(self.bySequence)
		completearray = []
		tot_debit = 0.0
		tot_credit = 0.0
		tot_scredit = 0.0
		tot_sdebit = 0.0
		tot_enlitige = 0.0
		for r in cleanarray:
			# For the first element we always add the line
			# type = 1 is the line is the first of the account
			# type = 2 is an other line of the account
			if i==0:
				# We add the first as the header
				#
				##
				new_header = {}
				new_header['ref'] = ''
				new_header['name'] = r['account_name']
				new_header['code'] = r['code']
				new_header['debit'] = 0
				new_header['credit'] = 0
				new_header['scredit'] = 0
				new_header['sdebit'] = 0
				new_header['sum_currency'] = 0
				new_header['currency_code'] = False
				new_header['balance'] = 0
				new_header['type'] = 3
				##
				completearray.append(new_header)
				#
				r['type'] = 1
				r['balance'] = float(r['sdebit']) - float(r['scredit'])
				completearray.append(r)
				#
				tot_debit = r['debit']
				tot_credit = r['credit']
				tot_scredit = r['scredit']
				tot_sdebit = r['sdebit']
				tot_enlitige = (r['sum_currency'] or 0.0)
				#
			else:
				if cleanarray[i]['account_id'] <> cleanarray[i-1]['account_id']:
					##
					new_tot = {}
					new_tot['ref'] = 'Total'
					new_tot['name'] = cleanarray[i-1]['account_name']
					new_tot['code'] = cleanarray[i-1]['code']
					new_tot['currency_code'] = self.get_currency_code_for_account(cleanarray[i-1]['account_id'])	
					new_tot['debit'] = tot_debit
					new_tot['credit'] = tot_credit
					new_tot['scredit'] = tot_scredit
					new_tot['sdebit'] = tot_sdebit
					new_tot['sum_currency'] = tot_enlitige
					new_tot['balance'] = float(tot_sdebit) - float(tot_scredit)
					new_tot['type'] = 3
					##
					completearray.append(new_tot)
					
					# we reset the counter 
					tot_debit = r['debit']
					tot_credit = r['credit']
					tot_scredit = r['scredit']
					tot_sdebit = r['sdebit']
					tot_enlitige = (r['sum_currency'] or 0.0)
					#
					##
					new_header = {}
					new_header['ref'] = ''
					new_header['name'] = r['account_name']
					new_header['code'] = r['code']
					new_header['debit'] = 0
					new_header['credit'] = 0
					new_header['scredit'] = 0
					new_header['sdebit'] = 0
					new_header['sum_currency'] = 0
					new_header['currency_code'] = False
					new_header['balance'] = 0
					new_header['type'] = 3
					##
					##
					completearray.append(new_header)
					##	
					#
					r['type'] = 1
					#
					r['balance'] = float(r['sdebit']) - float(r['scredit'])
					r['currency_code'] = self.get_currency_code_for_account(r['account_id'])
					#
					completearray.append(r)
				if cleanarray[i]['account_id'] == cleanarray[i-1]['account_id']:
					# we reset the counter 
					tot_debit = tot_debit + r['debit']
					tot_credit = tot_credit + r['credit']
					tot_scredit = tot_scredit + r['scredit']
					tot_sdebit = tot_sdebit + r['sdebit']
					tot_enlitige = tot_enlitige + (r['sum_currency'] or 0.0)
					#
					r['type'] = 2
					#
					r['balance'] = float(r['sdebit']) - float(r['scredit'])
					r['currency_code'] = self.get_currency_code_for_account(r['account_id'])
					#
					completearray.append(r)
			i = i + 1
		##
		new_tot = {}
		new_tot['ref'] = 'Total'
		new_tot['name'] = cleanarray[i-1]['account_name']
		new_tot['code'] = cleanarray[i-1]['code']
		new_tot['currency_code'] = self.get_currency_code_for_account(cleanarray[i-1]['account_id'])	
		new_tot['debit'] = tot_debit
		new_tot['credit'] = tot_credit
		new_tot['scredit'] = tot_scredit
		new_tot['sdebit'] = tot_sdebit
		new_tot['sum_currency'] = tot_enlitige
		new_tot['balance'] = float(tot_sdebit) - float(tot_scredit)
		new_tot['type'] = 3
		##
		completearray.append(new_tot)
		
		return completearray
	def get_currency_code_for_account(self,account_id):
		account_obj = pooler.get_pool(self.cr.dbname).get('account.account').browse(self.cr, self.uid, [account_id])
		if account_obj[0].currency_id:
			return account_obj[0].currency_id.code
		else:
			return False

	def _sum_debit(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		result_tmp = 0.0
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
					'SELECT sum(debit) ' \
					'FROM account_move_line AS l ' \
					'WHERE  ' \
						' account_id IN (' + self.account_ids + ') ' \
						'AND l.reconcile_id IS NULL ' \
						'AND date < %s ',
					(self.date_lst[0],))
			result_tmp = float(self.cr.fetchone()[0] or 0.0)
		#
		#
		self.cr.execute(
				'SELECT sum(debit) ' \
				'FROM account_move_line AS l ' \
				'WHERE  ' \
					' account_id IN (' + self.account_ids + ') ' \
					'AND l.date IN (' + self.date_lst_string + ') ' )
		result_tmp = result_tmp + float(self.cr.fetchone()[0] or 0.0)
		
		return result_tmp

	def _sum_credit(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		
		result_tmp = 0.0
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
					'SELECT sum(credit) ' \
					'FROM account_move_line AS l ' \
					'WHERE  ' \
						'  account_id IN (' + self.account_ids + ') ' \
						'AND l.reconcile_id IS NULL ' \
						'AND date < %s ' ,
				(self.date_lst[0],))
			result_tmp = float(self.cr.fetchone()[0] or 0.0)
		#
		#
		self.cr.execute(
				'SELECT sum(credit) ' \
				'FROM account_move_line AS l ' \
				'WHERE  ' \
					' account_id IN (' + self.account_ids + ') ' \
					'AND l.date IN (' + self.date_lst_string + ') ' )
				
		result_tmp = result_tmp + float(self.cr.fetchone()[0] or 0.0)
		
		return result_tmp

	def _sum_litige(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		result_tmp = 0.0
		
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
					'SELECT sum(debit-credit) ' \
					'FROM account_move_line AS l ' \
					'WHERE  ' \
						'  account_id IN (' + self.account_ids + ') ' \
						'AND l.reconcile_id IS NULL ' \
						'AND date < %s ' \
						'AND blocked=TRUE ' ,
				(self.date_lst[0],))
			result_tmp = float(self.cr.fetchone()[0] or 0.0)
		#
		#
		self.cr.execute(
				'SELECT sum(debit-credit) ' \
				'FROM account_move_line AS l ' \
				'WHERE  ' \
					'  account_id IN (' + self.account_ids + ') ' \
					'AND l.date IN (' + self.date_lst_string + ') ' \
					'AND blocked=TRUE ' )
		result_tmp = result_tmp + float(self.cr.fetchone()[0] or 0.0)
		
		return result_tmp
	

	def _sum_sdebit(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		result_tmp = 0.0
		
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
				'SELECT CASE WHEN sum(debit) > sum(credit) ' \
						'THEN sum(debit) - sum(credit) ' \
						'ELSE 0 ' \
					'END ' \
				'FROM account_move_line AS l  ' \
				'WHERE  ' \
					'  account_id IN (' + self.account_ids + ') ' \
					'AND date < %s ' \
					'AND reconcile_id IS NULL ' \
				'GROUP BY partner_id',
				(self.date_lst[0],))
			
			if self.cr.fetchone() != None:
				result_tmp = float(self.cr.fetchone()[0])
			else:
				result_tmp = 0.0
		#
		#
		self.cr.execute(
			'SELECT CASE WHEN sum(debit) > sum(credit) ' \
					'THEN sum(debit) - sum(credit) ' \
					'ELSE 0 ' \
				'END ' \
			'FROM account_move_line AS l ' \
			'WHERE  ' \
				'  account_id IN (' + self.account_ids + ') ' \
				'AND l.date IN (' + self.date_lst_string + ') ' \
			'GROUP BY partner_id')
		
		if self.cr.fetchone() != None:
			result_tmp = result_tmp + float(self.cr.fetchone()[0] or 0.0)
		else:
			result_tmp = 0.0
		return result_tmp		

	def _sum_scredit(self,data):
		if not self.ids:
			return 0.0
		account_move_line_obj = pooler.get_pool(self.cr.dbname).get('account.move.line')
		result_tmp = 0.0
		#
		#
		if data['form']['soldeinit'] :
			self.cr.execute(
				'SELECT CASE WHEN sum(debit) < sum(credit) ' \
						'THEN sum(credit) - sum(debit) ' \
						'ELSE 0 ' \
					'END ' \
				'FROM account_move_line AS l ' \
				'WHERE  ' \
					' account_id IN (' + self.account_ids + ') ' \
					'AND date <= %s ' \
					'AND l.reconcile_id IS NULL ' \
				'GROUP BY partner_id',
				(self.date_lst[0],))
			if self.cr.fetchone() != None:
				result_tmp = float(self.cr.fetchone()[0])
			else:
				result_tmp = 0.0
		#
		#
		self.cr.execute(
			'SELECT CASE WHEN sum(debit) < sum(credit) ' \
					'THEN sum(credit) - sum(debit) ' \
					'ELSE 0 ' \
				'END ' \
			'FROM account_move_line AS l ' \
			'WHERE   ' \
				' account_id IN (' + self.account_ids + ') ' \
				'AND l.date IN (' + self.date_lst_string + ') ' \
			'GROUP BY partner_id')
		
		if self.cr.fetchone() != None:
			result_tmp = result_tmp + float(self.cr.fetchone()[0] or 0.0)
		else:
			result_tmp = 0.0
		
		return result_tmp
	
	def _solde_balance_debit(self,data):
		debit, credit = self._sum_debit(data), self._sum_credit(data)
		return debit > credit and debit - credit
		
	def _solde_balance_credit(self,data):
		debit, credit = self._sum_debit(data), self._sum_credit(data)
		return credit > debit and credit - debit

	def _get_company(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).name

	def _get_currency(self, form):
		return pooler.get_pool(self.cr.dbname).get('res.company').browse(self.cr, self.uid, form['company_id']).currency_id.name

report_sxw.report_sxw('report.account.partner.balancec2c', 'res.partner',
	'c2c_finance_report/partner_balance.rml',parser=partner_balancec2c,
	header=False)

