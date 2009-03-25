##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#                    Fabien Pinckaers <fp@tiny.Be>
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
import pooler


# dates_form = '''<?xml version="1.0"?>
# <form string="Select period and journal">
# 	<field name="fiscalyear" colspan="4"/>
# 	<field name="periods" colspan="4"/>
# 	<field name="journal" colspan="4"/>	
# </form>'''
# 
# dates_fields = {
# 	'fiscalyear': {'string': 'Fiscal year', 'type': 'many2one', 'relation': 'account.fiscalyear',
# 		'help': 'Keep empty for all open fiscal year'},
# 	'periods': {'string': 'Periods', 'type': 'many2many', 'relation': 'account.period', 'help': 'All periods if empty'},
# 	'journal':{'string':"Journal:", 'type': 'many2one', 'relation': 'account.journal'},
# }
dates_form = '''<?xml version="1.0"?>
<form string="Choose the sort order :">
	<field name="sort_1" colspan="4"/>
	<field name="sort_2" colspan="4"/>
	<field name="sort_3" colspan="4"/>
</form>'''

dates_fields = {
	'sort_1':{'string':"1st sort by:",'default':'date','type':'selection','selection':[('date','Date'),('debit','Debit'),('credit','Credit'),('account_id','Account'),('partner_id','Partner'),('move_id','Movement')]},
	'sort_2':{'string':"2nd sort by:",'type':'selection','selection':[('date','Date'),('debit','Debit'),('credit','Credit'),('account_id','Account'),('partner_id','Partner'),('move_id','Movement')]},
	'sort_3':{'string':"3rd sort by:",'type':'selection','selection':[('date','Date'),('debit','Debit'),('credit','Credit'),('account_id','Account'),('partner_id','Partner'),('move_id','Movement')]},
}

# def _action_open_window(self, cr, uid, data, context):
# 	mod_obj = pooler.get_pool(cr.dbname).get('ir.model.data')
# 	act_obj = pooler.get_pool(cr.dbname).get('ir.actions.act_window')
# 
# 	result = mod_obj._get_id(cr, uid, 'account', 'action_move_line_select')
# 	id = mod_obj.read(cr, uid, [result], ['res_id'])[0]['res_id']
# 	result = act_obj.read(cr, uid, [id])[0]
# 
# 	cr.execute('select journal_id,period_id from account_journal_period where id=%d', (data['id'],))
# 	journal_id,period_id = cr.fetchone()
# 
# 	result['domain'] = str([('journal_id', '=', journal_id), ('period_id', '=', period_id)])
# 	result['context'] = str({'journal_id': journal_id, 'period_id': period_id})
# 	return result
					
class wiz_journalc2c(wizard.interface):
	
	# def _get_defaults(self, cr, uid, data, context):
	# 	fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
	# 	data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
	# 	return data['form']

	states = {
		'init': {
			'actions': [],
			'result': {'type':'form', 'arch':dates_form, 'fields':dates_fields, 'state':[('end','Cancel'),('report','Print')]}
		},
		'report': {
			'actions': [],
			'result': {'type':'print', 'report':'account.journal.movec2c', 'state':'end'}
		}
	}
wiz_journalc2c('account.journal.movec2c')
