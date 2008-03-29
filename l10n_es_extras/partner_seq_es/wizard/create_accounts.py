#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: make_picking.py 1070 2005-07-29 12:41:24Z nicoe $
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

import wizard
import netsvc
import pooler

accounts_create_form = """<?xml version="1.0"?>
<form string="Create accounts">
	<separator string="Do you want to create accounts for the selected partners" />
</form>"""

accounts_create_fields = {}

def strip0d(cadena):
	# Elimina los ceros de la derecha en una cadena de texto de dígitos
	return str(int(cadena[::-1]))[::-1]   
	
def strip0i(cadena):
	# Elimina los ceros de la izquierda en una cadena de texto de dígitos
	return str(int(cadena))
	 

def _createAccounts(self, cr, uid, data, context):
	partner_obj = pooler.get_pool(cr.dbname).get('res.partner')
	account_obj = pooler.get_pool(cr.dbname).get('account.account')
	sequence_obj = pooler.get_pool(cr.dbname).get('ir.sequence')
	
	def link_account(ref,parent_code, acc_type, acc_property):
		# parent_code: Código del padre (Ej.: 4300)
		# type: Puede ser 'payable' o 'receivable'
		# acc_property: 'property_account_receivable' o 'property_account_payable'
		acc_code = parent_code + ref[2:]  # acc_code es el nuevo código de subcuenta	  
		args = [('code', '=', acc_code)]
		if not account_obj.search(cr, uid, args):
			args = [('code', '=', parent_code)]
			parent_acc_ids = account_obj.search(cr, uid, args) # Busca id de la subcuenta padre
			vals = {
			'name': partner.name,
			'code': acc_code,
			'type': acc_type,
			'parent_id': [(6,0,parent_acc_ids)], # acc_ids es un diccionario
			'sign': 1,
			'close_method': 'unreconciled',
			'shortcut': strip0d(acc_code[:4]) + "." + strip0i(acc_code[-5:]),
			}
			acc_id = account_obj.create(cr, uid, vals)		   
			vals = {acc_property: acc_id}
			partner_obj.write(cr, uid, [partner.id], vals)	 # Asocia la nueva subcuenta con el partner
	   
	for partner in partner_obj.browse(cr, uid, data['ids'], context=context):
		if not partner.ref or not partner.ref.strip():
			ref = sequence_obj.get(cr, uid, 'res.partner')
			vals = {'ref': ref}
			partner_obj.write(cr, uid, [partner.id], vals)
		else:
			 ref =  partner.ref  
						
		if (len(ref) == 7) and (ref[2:].isdigit()):			
			for category in partner.category_id:
				if category.name.lower() == 'cliente':
					link_account(ref,'4300', 'receivable', 'property_account_receivable')

				if category.name.lower() == 'proveedor':
					link_account(ref,'4000', 'payable', 'property_account_payable')
	return {}


class create_accounts(wizard.interface):
	states = {
		'init' : {
			'actions' : [],
			'result' : {'type' : 'form',
					'arch' : accounts_create_form,
					'fields' : accounts_create_fields,
					'state' : [('end', 'Cancel'),('create', 'Create accounts') ]}
		},
		'create' : {
			'actions' : [],
			'result' : {'type' : 'action',
					'action' : _createAccounts,
					'state' : 'end'}
		},
	}
create_accounts("partner_seq.create_accounts")
