# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo - Account summary
#    Copyright (C) 2014 Luis Martinez Ontalba (www.tecnisagra.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import tools
from osv import fields,osv
import decimal_precision as dp

class account_account(osv.osv):
    _name = "account.account"
    _inherit = "account.account"
	
    def _get_code_2(self, cr, uid, ids, field_name, arg, context=None):
        result={}
        acc_obj = self.browse(cr,uid,ids,context=context)
        for acc in acc_obj:
			result[acc.id]= acc.code[0:2]
        return result
	
    _columns = {
        'code_2' : fields.function(_get_code_2, string = 'Código corto', method=True, type='char', store=True)
    }

account_account()	
	

class account_summary(osv.osv):

    _name = "account.summary"
    _auto = False
    _columns = {
        'debit': fields.float('Debe', readonly=True),
        'credit': fields.float('Haber', readonly=True),
        'balance': fields.float('Balance', readonly=True),
        'balance_inv': fields.float('Balance inverso', readonly=True),
        'account_code': fields.char('Cuenta', size=8, readonly=True),
        'year': fields.char('Año', size=4, readonly=True),
        'date': fields.date('Fecha', size=128, readonly=True),
        'period_id': fields.many2one('account.period', 'Periodo', readonly=True),
        'account_id': fields.many2one('account.account', 'Cuenta', readonly=True),
		'fiscalyear_id': fields.many2one('account.fiscalyear', 'Año fiscal', readonly=True),
    }

    _order = 'date desc'


    def init(self, cr):
        tools.drop_view_if_exists(cr, 'account_summary')
        cr.execute("""
            create or replace view account_summary as (
            select
                l.id as id,
                am.date as date,
                to_char(am.date, 'YYYY') as year,
                p.fiscalyear_id as fiscalyear_id,
                am.period_id as period_id,
                l.account_id as account_id,
				a.code_2 as account_code,
                l.debit as debit,
                l.credit as credit,
                l.debit-l.credit as balance,
                l.credit-l.debit as balance_inv
            from
                account_move_line l
                left join account_account a on (l.account_id = a.id)
                left join account_move am on (am.id=l.move_id)
                left join account_period p on (am.period_id=p.id)
                where l.state != 'draft'
            )
        """)

account_summary()


