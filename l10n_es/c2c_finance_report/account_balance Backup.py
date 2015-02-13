# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2004-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
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
from report import report_sxw
import xml
import rml_parse

class account_balancec2c(rml_parse.rml_parse):
	_name = 'report.account.account.balancec2c'
	def __init__(self, cr, uid, name, context):
		super(account_balancec2c, self).__init__(cr, uid, name, context)
		self.sum_debit = 0.0
		self.sum_credit = 0.0
		self.tot_debit = 0.0
		self.tot_credit = 0.0
		self.localcontext.update({
							
			'time': time,
			'lines': self.lines,
			'sum_debit': self._sum_debit,
			'sum_credit': self._sum_credit,
			'sum_balance': self._sum_balance,
		})
		self.context = context

	def lines(self, form, ids={}, done=None, level=1,):
		if not ids:
			ids = self.ids
		if not ids:
			return []
		if not done:
			done={}
		result = []
		ctx = self.context.copy()
		ctx['fiscalyear'] = form['fiscalyear']
		ctx['periods'] = form['periods'][0][2]
		accounts = self.pool.get('account.account').browse(self.cr, self.uid, ids, ctx)
		def cmp_code(x, y):
			return cmp(x.code, y.code)
		accounts.sort(cmp_code)
		for account in accounts:
			if account.id in done:
				continue
			done[account.id] = 1
			res = {
				'code': account.code + ' ' + account.name,
				'level': level,
				'debit': account.debit,
				'credit': account.credit,
				'balance': account.balance,
				'type' : 1
			}
			self.sum_debit += account.debit
			self.sum_credit += account.credit
			#if (res['level'] < 6):
			#	res['name'] = res['name'].upper()
			header = {
				'code': account.name,
				'level': level,
				'debit': account.debit,
				'credit': account.credit,
				'balance': 0,
				'type' : 5
			}
							
			if ((res['level'] >= 2) and (res['level'] <= 5)):
				res['code'] = account.name
				res['type'] = 2
				result.append(header)
				#header['code'] = header['code'].upper()
				#if (header['credit'] or header['debit'] or header['balance']):
			if not (res['credit'] or res['debit']) and not account.child_id:
				continue
			if account.child_id:
				ids2 = [(x.code,x.id) for x in account.child_id]
				ids2.sort()
				result += self.lines(form, [x[1] for x in ids2], done, level+1,)
			if (res['credit'] or res['debit'] or res['balance']):
				result.append(res)
				separator = {
					'code': '',
					'level': level,
					'debit': 0,
					'credit': 0,
					'balance': 0,
					'type' : 3
				}
				total = {
					'code': '',
					'level': level,
					'debit': self.sum_debit,
					'credit': self.sum_credit,
					'balance': (self.sum_debit - self.sum_credit) ,
					'type' : 6
				}
				
				result.append(separator)
				result.append(total)
		return result

	def _sum_credit(self):
		return self.sum_credit

	def _sum_debit(self):
		return self.sum_debit
	
	def _sum_balance(self):
		return self.sum_debit - self.sum_credit

#report_sxw.report_sxw('report.account.account.balance', 'account.account', 'addons/account/report/account_balance.rml', parser=account_balance, header=False)
report_sxw.report_sxw('report.account.account.balancec2c', 'account.account', 'addons/c2c_finance_report/account_balance.rml', parser=account_balancec2c, header=False)


