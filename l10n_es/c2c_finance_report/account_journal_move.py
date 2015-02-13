##############################################################################
#
# Copyright (c) 2005-2006 CamptoCamp
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
from mx.DateTime import *
from report import report_sxw
import xml
import rml_parse


class journal_movec2c(rml_parse.rml_parse):
	_name = 'report.account.journal.movec2c'
	def __init__(self, cr, uid, name, context):
		super(journal_movec2c, self).__init__(cr, uid, name, context)
		self.localcontext.update( {
			'time': time,
			# 'lines': self.lines,
			# 'sum_debit_account': self._sum_debit_account,
			# 'sum_credit_account': self._sum_credit_account,
			# 'sum_solde_account': self._sum_solde_account,
			'sum_debit': self._sum_debit,
			'sum_credit': self._sum_credit,
			# 'sum_solde': self._sum_solde, 
			# 'get_children_accounts': self.get_children_accounts
			'get_ordred_lines': self.get_ordred_lines,
			'format_date': self._get_and_change_date_format_for_swiss,
		})
		self.context = context

	def _get_and_change_date_format_for_swiss (self,date_to_format):
		date_formatted=''
		if date_to_format:
			date_formatted = strptime (date_to_format,'%Y-%m-%d').strftime('%d.%m.%Y')
		else:
			date_formatted=''
		return date_formatted

	def get_ordred_lines(self, account_lines, form):
		res = []
		list_ids_unsorted = []
		# Get the ids
		for line in account_lines:
			list_ids_unsorted.append(line.id)
		#Construct order by cluse
		order_cl=' ORDER BY '
		if form['sort_1']:
			order_cl = order_cl + form['sort_1']
			if form['sort_2']:
				order_cl = order_cl + ',' + form['sort_2']
			if form['sort_3']:
				order_cl = order_cl + ',' + form['sort_3']
		# Default by date
		else:
			order_cl=order_cl + 'date'
		# Sort the ids by selected sort
		self.cr.execute("SELECT id FROM account_move_line WHERE id in (%s) %s"%(','.join(map(str,list_ids_unsorted)),order_cl))
		req_sql = self.cr.dictfetchall()
		list_ids_sorted=[]
		for id in req_sql:
			list_ids_sorted.append(id['id'])
		res=self.pool.get('account.move.line').browse(self.cr,self.uid,list_ids_sorted)
		return res

	def _sum_debit(self, account_lines):
		res=0
		for line in account_lines:
			res=res+line.debit
		return res
		
	def _sum_credit(self, account_lines):
		res=0
		for line in account_lines:
			res=res+line.credit
		return res

	def _sum_solde(self, form):
		if not self.ids:
			return 0.0
		child_ids = self.pool.get('account.account').search(self.cr, self.uid,
			[('parent_id', 'child_of', self.ids)])
		ctx = self.context.copy()
		ctx['fiscalyear'] = form['fiscalyear']
		ctx['periods'] = form['periods'][0][2]
		query = self.pool.get('account.move.line')._query_get(self.cr, self.uid, context=ctx)
		period_sql = ''
		if ctx['periods'] :
			period_sql = " AND l.period_id in (%s)"%(",".join(map(str,ctx['periods'])))
		self.cr.execute("SELECT (sum(debit) - sum(credit)) as tot_solde "\
				"FROM account_move_line l "\
				"WHERE l.account_id in ("+','.join(map(str, child_ids))+") AND "+query+period_sql)
#		print ("SELECT (sum(debit) - sum(credit)) as Test "\
#				"FROM account_move_line l "\
#				"WHERE l.account_id in ("+','.join(map(str, child_ids))+") AND "+query+period_sql)
		return self.cr.fetchone()[0] or 0.0
	

report_sxw.report_sxw('report.account.journal.movec2c', 'account.move.line', 'addons/c2c_finance_report/account_journal_move.rml', parser=journal_movec2c, header=False)
