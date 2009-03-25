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
import copy
from operator import itemgetter

class account_chartc2c(rml_parse.rml_parse):
	_name = 'report.account.account.chartc2c'
	gadr_cpt = 0
	def __init__(self, cr, uid, name, context):
		super(account_chartc2c, self).__init__(cr, uid, name, context)
		self.localcontext.update({
			'time': time,
			'lines': self.lines,
		})
		self.context = context
		
	def preprocess(self, objects, data, ids):
		new_ids = []
		if (data['model'] == 'account.account'):
			new_ids = ids
		else:
			new_ids.append(data['form']['Account_list'])
			objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
			
		super(account_chartc2c, self).preprocess(objects, data, new_ids)	

	def lines(self,ids={}, done=None, level=1):
		retour_unsort = self.get_result(ids,done)
		return self.sort_result(retour_unsort,31)
	
	def sort_result(self,account,rupture):
		max_level = self.max_level_search(account)
		if not account :
			return []
		ind_type = 0
		ind_rup = 0
		account_result = []
		while ind_type < len(account):
			account_elem = account[ind_type]
			res_sort = {
				'code' : account_elem['code'],
				'name':  account_elem['name'],
				'name_dr': '',
				'type_gd' : 1,
				'type_dr' : 1
			}
			if account_elem['level'] < max_level:
				res_sort['type_gd'] = 2;
				res_sort['name_gd'] = account_elem['name']
#			ind_type_dr = ind_type + rupture;
#			if (ind_type_dr >= len(account)):
#				account_result.append(res_sort)
#				ind_rup+=1
#				ind_type+=1
#				continue
#			account_elem = account[ind_type_dr]
#			res_sort['name_dr'] = account_elem['code']+ ' ' + account_elem['name']
#			if account_elem['level'] < 5:
#				res_sort['type_dr'] = 2
#				res_sort['name_dr'] = account_elem['name']
#				
#			print ind_type_dr
			account_result.append(res_sort)
			ind_rup+=1
			ind_type+=1
			# si on a remplis une page on fait la rupture de la page
#			if (ind_rup >= rupture):
#				# On multiplie la rupture par 2 pour repositionner le tableau correctement
#				ind_rup = 0 
#				ind_type = ind_type + rupture
			
		return account_result

	def get_result(self,ids={},done=None,level=1):
		if not ids:
			ids = self.ids
		if not ids:
			return []
		if not done:
			done={}
		result = []
		accounts = self.pool.get('account.account').browse(self.cr, self.uid, ids,self.context)
		def cmp_code(x, y):
			return cmp(x.code, y.code)
		accounts.sort(cmp_code)
		for account in accounts:
			if account.id in done:
				continue
			done[account.id] = 1
			res = {
				'code': account.code,
				'name' : account.name,
				'type': 1,
				'level': level
			}
			result.append(res)
			if account.child_id:
				ids2 = [(x.code,x.id) for x in account.child_id]
				ids2.sort()
				result += self.get_result([x[1] for x in ids2], done,level+1)
		return result

	def max_level_search(self,account_list):
		result = sorted(account_list, key=itemgetter('level'))
		if (result):
			return result[len(result)-1]['level']
		else:
			return 0
#report_sxw.report_sxw('report.account.account.balance', 'account.account', 'addons/account/report/account_balance.rml', parser=account_balance, header=False)
report_sxw.report_sxw('report.account.account.chartc2c', 'account.account','addons/c2c_finance_report/account_chart.rml', parser=account_chartc2c, header=False)


