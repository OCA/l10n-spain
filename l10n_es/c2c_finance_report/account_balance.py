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

class account_balancec2c(rml_parse.rml_parse):
	_name = 'report.account.account.balancec2c'
	
	def preprocess(self, objects, data, ids):
		new_ids = []
		if (data['model'] == 'account.account'):
			new_ids = ids
		else:
			new_ids.append(data['form']['Account_list'])
			
			objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
			
		super(account_balancec2c, self).preprocess(objects, data, new_ids)	

	
	def __init__(self, cr, uid, name, context):
		super(account_balancec2c, self).__init__(cr, uid, name, context)
		self.sum_debit = 0.0
		self.sum_credit = 0.0
		self.localcontext.update({
			'time': time,
			'lines': self.lines,
			'sum_debit': self._sum_debit,
			'sum_credit': self._sum_credit,
			'sum_balance': self._sum_balance,
		})
		self.context = context

	def lines(self, form, ids={}, done=None, level=1,):
		resultat = self.get_result(form, ids,done,level)
		#sort_result = self.sort_account(resultat)
		return resultat
#		print resultat
#		result = []
#		return sort_result
	def get_result(self,form,ids={},done=None,level=1):
		if not ids:
			ids = self.ids
		if not ids:
			return []
		if not done:
			done={}
		result = []
		ctx = self.context.copy()
		## We will now make the test
		#
		if form.has_key('fiscalyear'): 
			ctx['fiscalyear'] = form['fiscalyear']
			ctx['periods'] = form['periods'][0][2]
		else:
			ctx['date_from'] = form['date_from']
			ctx['date_to'] = form['date_to']
		##
		#
		accounts = self.pool.get('account.account').browse(self.cr, self.uid, ids, ctx)
		def cmp_code(x, y):
			return cmp(x.code, y.code)
		accounts.sort(cmp_code)
				
		# Get the credit/debit with fiscal year / period filter
		all_debit=self.pool.get('account.account')._debit(self.cr,self.uid,ids,'debit',[],ctx)
		all_credit=self.pool.get('account.account')._credit(self.cr,self.uid,ids,'credit',[],ctx)
		for account in accounts:
			if account.id in done:
				continue
			# Modif for Reviseur des comptes
			#if account.balance < 0:
			#	balance_inv = abs(account.balance)
			#else:
			#	balance_inv = account.balance * -1
			done[account.id] = 1
			res = {
				'code': account.code,
				'name': account.name,
				'level': level,
				'debit': abs(all_debit[account.id]),
				'credit': abs(all_credit[account.id]),
				#'balance': balance_inv,
				'balance': account.balance,
				'account_type':account.type,
				'child_id_sw' : (account.child_id and 1 or 0) , 
				'type': 1,
				'pos': 1,
			}

			self.sum_debit += abs(all_debit[account.id]) #account.debit
			self.sum_credit += abs(all_credit[account.id]) #account.credit
			
			#print str(account.code) + "@@" + str(self.sum_debit) + "##" + str(self.sum_credit)
#			if  not account.child_id:
#				continue
			if form['display_account'] == 'bal_mouvement':
				if res['credit'] <> 0 or res['debit'] <> 0 or res['balance'] <> 0:
					result.append(res)
			elif form['display_account'] == 'bal_solde':		
				if  res['balance'] <> 0:
					result.append(res)
			else:
				result.append(res)
			if account.child_id:
				ids2 = [(x.code,x.id) for x in account.child_id]
				ids2.sort()
				result += self.get_result(form, [x[1] for x in ids2], done, level+1)
		return result
	
	def sort_account(self,accounts=[]):
		result_accounts=[]
		if accounts==[]:
		  return []
		result = {
				'code': '',
				'name': '',
				'level': 99,
				'debit': '',
				'credit': '',
				'balance': '',
				'type': 0,
				'child_id_sw' : 0,
				'pos' : 0
			} 
		res = {
				'code': '',
				'name': '',
				'level': 99,
				'debit': '',
				'credit': '',
				'balance': '',
				'type': 0,
				'child_id_sw' : 0,
				'pos' : 0
			} 

		#
		#
		#
		max_lenth = self.max_level_search(accounts)
		tree_struct = {}
		for i in range(max_lenth+1):
			tree_struct[str(i)] = copy.copy(res)
		#
		#
		#
		#print str(tree_struct)
		#tree_struct={'0':res,'1': res1,'2': res2,'3': res3,'4': res4,'5': res5,'6': res6,'7': res7}
		ind_tab=0
		tab_rup=9999
		old_level=1
		result_account = copy.deepcopy(accounts)
		while (ind_tab < len(accounts)):
			
			## we will test the rupture sequence
			if (tab_rup == 9999):
				tab_rup = ind_tab
			##
			
			##
			
			account_elem = copy.deepcopy(accounts[ind_tab])
			
			## we will compare level and if we will test if
			if (old_level > account_elem['level']):
				tmp_ind = old_level 
				while (tmp_ind >= account_elem['level'] ):
#					print "TMP id" + str(tmp_ind) + " Current Level" + str(account_elem['level'])
					# on construit un nouvel element
					new_item = copy.deepcopy(result)
					# pour ce type d'affichage
					# Ne pas le faire pour la première ligne du rapport
					new_item['code'] = 'Total : ' + tree_struct[str(tmp_ind)]['code'] 
					new_item['name'] = tree_struct[str(tmp_ind)]['name']
					new_item['level'] = tree_struct[str(tmp_ind)]['level']
					new_item['debit'] = tree_struct[str(tmp_ind)]['debit'] 
					new_item['credit'] = tree_struct[str(tmp_ind)]['credit']
					new_item['balance'] = tree_struct[str(tmp_ind)]['balance']
					new_item['type'] = 2
					# on insère ce nouvel élément dans la structure
					##
					#print new_item
					if (tree_struct[str(tmp_ind)]['child_id_sw'] == 0):
						tmp_ind -= 1
					else:
						result_account.insert(tab_rup,new_item)
						tmp_ind -= 1
						tab_rup += 1
						
					# on change juste le type pour imprimer in ligne et on ajoute
					# on incrémente le compteur de boucle
					# on remet l'élément à vide
					if (tree_struct[str(tmp_ind)]['child_id_sw'] <> 0):
						result_account[tree_struct[str(tmp_ind)]['pos']]['type'] = 6
						result_account[tree_struct[str(tmp_ind)]['pos']]['code'] = tree_struct[str(tmp_ind)]['code']
						result_account[tree_struct[str(tmp_ind)]['pos']]['credit'] = 0
						result_account[tree_struct[str(tmp_ind)]['pos']]['debit'] = 0
						result_account[tree_struct[str(tmp_ind)]['pos']]['balance'] = 0
						
					tree_struct[str(tmp_ind)]['level'] = 99
					#tmp_ind -= 1
					#tab_rup += 1
					# maintenant que l'on a modifier la rupture finale on va modifier le type du compte précédent
					
					
			##
			## on va tester que l'elements presents n'est pas dￃﾩjￃﾠￃﾨ insￃﾩrer dans notre dictionnaire
			if tree_struct[str(account_elem['level'])]['level'] == 99:
				tree_struct[str(account_elem['level'])]['code'] = account_elem['code']
				tree_struct[str(account_elem['level'])]['level'] = account_elem['level']
				tree_struct[str(account_elem['level'])]['name'] = account_elem['name']
				tree_struct[str(account_elem['level'])]['debit'] = account_elem['debit']
				tree_struct[str(account_elem['level'])]['credit'] = account_elem['credit']
				tree_struct[str(account_elem['level'])]['balance'] = account_elem['balance']
				tree_struct[str(account_elem['level'])]['child_id_sw'] = account_elem['child_id_sw']
				tree_struct[str(account_elem['level'])]['type'] = 6
				tree_struct[str(account_elem['level'])]['pos'] = tab_rup
				
			# 
			old_level = account_elem['level'] 
			ind_tab+=1
			tab_rup+=1
		
		for i in reversed(range(max_lenth)):
			##if tree_struct[str(i)]['level'] <> 99:
				tab_rup+=1
				tree_struct[str(i)]['code'] = 'Total : ' + tree_struct[str(i)]['code']
				tree_struct[str(i)]['type'] = 2
				
				result_account.insert(tab_rup,tree_struct[str(i)])
				
				result_account[tree_struct[str(i)]['pos']]['type'] = 2
				result_account[tree_struct[str(i)]['pos']]['code'] = tree_struct[str(i)]['code']
				result_account[tree_struct[str(i)]['pos']]['name'] = tree_struct[str(i)]['name']
				result_account[tree_struct[str(i)]['pos']]['credit'] = 0
				result_account[tree_struct[str(i)]['pos']]['debit'] = 0
				result_account[tree_struct[str(i)]['pos']]['balance'] = 0
		
		return result_account



	#def sort_account(self,accounts):
	#	# On boucle sur notre rapport
	#	result_accounts = []
	#	ind=0
	#	old_level=0
	#	max_level = self.max_level_search(accounts) 
	#	print str(max_level)
	#	while ind<len(accounts):
	#		
	#
	#		#
	#		account_elem = accounts[ind]
	#		#
	#		
	#		#
	#		# we will now check if the level is lower than the previous level, in this case we will make a subtotal
	#		if (account_elem['level'] < old_level):
	#			bcl_current_level = old_level
	#			bcl_rup_ind = ind - 1
	#			
	#			while (bcl_current_level >= int(accounts[bcl_rup_ind]['level']) and bcl_rup_ind >= 0 and account_elem['level'] <= bcl_current_level ):
	#				tot_elem = copy.copy(accounts[bcl_rup_ind])
	#				res_tot = { 'code' : accounts[bcl_rup_ind]['name'],
	#					'name' : '',
	#					'debit' : 0,
	#					'credit' : 0,
	#					'balance' : accounts[bcl_rup_ind]['balance'],
	#					'type' : accounts[bcl_rup_ind]['type'],
	#					'level' : 0,
	#					'pos' : 0
	#				}
	#				# On spécifie que l'on a imprimer ce total
	#				accounts[bcl_rup_ind]['pos'] = 2
	#				# on change le type pour afficher le total
	#				res_tot['type'] = 2
	#				res_tot['code'] = 'Total : ' +  res_tot['code']
	#				# On teste si on est pas dans le cas d'un compte de dernier niveau
	#				if (accounts[bcl_rup_ind]['level'] < max_level):
	#					print "BCL" + str(bcl_current_level) + "@@" + str(accounts[bcl_rup_ind]['level']) + "Account Name :" + str(accounts[bcl_rup_ind]['code']) +  "Current Level :" + str(account_elem['level'])
	#					result_accounts.append(res_tot)
	#				bcl_current_level =  accounts[bcl_rup_ind]['level']
	#				bcl_rup_ind -= 1
	#		old_level = account_elem['level']
	#		
	#		# We will add the account but in case of a parent node we will mark it in bold
	#		#if (account_elem['level'] < max_level):
	#		#	result_accounts.append(account_elem)
	#		#	result_accounts[len(result_accounts)-1]['type'] = 2
	#		#	result_accounts[len(result_accounts)-1]['debit'] = 0
	#		#	result_accounts[len(result_accounts)-1]['credit'] = 0
	#		#	
	#		#	
	#		#else:
	#		result_accounts.append(account_elem)
	#		ind+=1
	#	self.get_unprint_tot(accounts)
	#	return result_accounts
	
	def max_level_search(self,account_list):
		result = sorted(account_list, key=itemgetter('level'))
		if (result):
			return result[len(result)-1]['level']
		else:
			return 0

	def get_unprint_tot(self,account_list):
		result = sorted(account_list, key=itemgetter('pos'))
		for account_line in result:
			if account_line['pos'] == 1:
				print account_line['code'] + str(account_line['level'])
		


	def _sum_credit(self):
		return self.sum_credit

	def _sum_debit(self):
		return self.sum_debit
	
	def _sum_balance(self):
		return self.sum_debit - self.sum_credit

#report_sxw.report_sxw('report.account.account.balance', 'account.account', 'addons/account/report/account_balance.rml', parser=account_balance, header=False)
report_sxw.report_sxw('report.account.account.balancec2c', 'account.account', 'addons/c2c_finance_report/account_balance.rml', parser=account_balancec2c, header=False)


