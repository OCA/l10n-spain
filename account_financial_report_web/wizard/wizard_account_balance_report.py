# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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

import wizard
import pooler
import time
import report
from osv import osv, fields
from tools.translate import _

class fl_account_balance_full_report(osv.osv_memory):

    _name = 'fl.account.balance.full.report'
    _columns = {

        'company_id': fields.many2one('res.company','Company',required=True),
        'account_list':fields.many2many('account.account', 'balance_full_account_rel2', 'balance_id','account_id','Root accounts', required=True),
        'state':fields.selection((('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')),
                   'Date/Period Filter'),
        'fiscalyear':fields.many2one('account.fiscalyear', 'Fiscal year', required=True, help='Keep empty to use all open fiscal years to compute the balance'),
        'periods':fields.many2many('account.period', 'balance_full_period_rel2', 'balance_id','period_id', 'Periods', help='All periods in the fiscal year if empty'),
        'display_account':fields.selection((('bal_all','All'),('bal_solde', 'With balance'),('bal_mouvement','With movements')),'Display accounts '),
        'display_account_level':fields.integer('Up to level', help='Display accounts up to this level (0 to show all)'),
        'date_from':fields.date('Start date',required=True),
        'date_to':fields.date('End date',required=True),
    }
    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-%m-%d'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'state': lambda *a:'none',
        'display_account_level': lambda *a: 0,
        'company_id': lambda self,cr,uid,c: self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=c),
        'fiscalyear': lambda self, cr, uid, c: self.pool.get('account.fiscalyear').find(cr, uid),
        'display_account': lambda *a:'bal_all',
    }

    def onchange_company_id(self,cr,uid,ids,company_id,context=None):
        if context is None:
            context = {}
        context['company_id']=company_id
        res = {'value':{}}
        
        if not company_id:
            return res
            
        cur_id = self.pool.get('res.company').browse(cr,uid,company_id,context=context).currency_id.id
        fy_id = self.pool.get('account.fiscalyear').find(cr, uid,context=context)
        res['value'].update({'fiscalyear':fy_id})
        res['value'].update({'account_list':[]})
        res['value'].update({'periods':[]})
        return res

    def _get_defaults(self, cr, uid, data, context=None):
        if context is None:
            context = {}
        user = pooler.get_pool(cr.dbname).get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
           company_id = user.company_id.id
        else:
           company_id = pooler.get_pool(cr.dbname).get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['form']['company_id'] = company_id
        fiscalyear_obj = pooler.get_pool(cr.dbname).get('account.fiscalyear')
        data['form']['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        data['form']['context'] = context
        return data['form']


    def _check_state(self, cr, uid, data, context=None):

        if context is None:
            context = {}
        if data['form']['state'] == 'bydate':
           self._check_date(cr, uid, data, context)
        return data['form']
    
    def _check_date(self, cr, uid, data, context=None):
        if context is None:
            context = {}
            
        if data['form']['date_from'] > data['form']['date_to']:
            raise osv.except_osv(_('Error !'),('La fecha final debe ser mayor a la inicial'))
        
        sql = """SELECT f.id, f.date_start, f.date_stop
            FROM account_fiscalyear f
            WHERE '%s' = f.id """%(data['form']['fiscalyear'][0])
        cr.execute(sql)
        res = cr.dictfetchall()

        if res:
            if (data['form']['date_to'] > res[0]['date_stop'] or data['form']['date_from'] < res[0]['date_start']):
                raise osv.except_osv(_('UserError'),'Las fechas deben estar entre %s y %s' % (res[0]['date_start'], res[0]['date_stop']))
            else:
                return 'report'
        else:
            raise osv.except_osv(_('UserError'),'No existe periodo fiscal')

    def period_span(self, cr, uid, ids, fy_id, context=None):
        if context is None:
            context = {}
        ap_obj = self.pool.get('account.period')
        fy_id = fy_id and type(fy_id) in (list,tuple) and fy_id[0] or fy_id
        if not ids:
            #~ No hay periodos
            return ap_obj.search(cr, uid, [('fiscalyear_id','=',fy_id),('special','=',False)],order='date_start asc')
        
        ap_brws = ap_obj.browse(cr, uid, ids, context=context)
        date_start = min([period.date_start for period in ap_brws])
        date_stop = max([period.date_stop for period in ap_brws])
        return ap_obj.search(cr, uid, [('fiscalyear_id','=',fy_id),('special','=',False),('date_start','>=',date_start),('date_stop','<=',date_stop)],order='date_start asc')
        

    def print_report(self, cr, uid, ids, data, context=None):

        if context is None:
            context = {}
            
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])
        if data['form']['state'] == 'byperiod':
            del data['form']['date_from']
            del data['form']['date_to']

            data['form']['periods'] = self.period_span(cr, uid, data['form']['periods'], data['form']['fiscalyear'])

        elif data['form']['state'] == 'bydate':
            self._check_date(cr, uid, data)
            del data['form']['periods']
        elif data['form']['state'] == 'none':
            del data['form']['date_from']
            del data['form']['date_to']
            del data['form']['periods']
        else:
            self._check_date(cr, uid, data)
            lis2 = str(data['form']['periods']).replace("[","(").replace("]",")")
            sqlmm = """select min(p.date_start) as inicio, max(p.date_stop) as fin 
            from account_period p 
            where p.id in %s"""%lis2
            cr.execute(sqlmm)
            minmax = cr.dictfetchall()
            if minmax:
                if (data['form']['date_to'] < minmax[0]['inicio']) or (data['form']['date_from'] > minmax[0]['fin']):
                    raise osv.except_osv(_('Error !'),_('La interseccion entre el periodo y fecha es vacio'))

        return {'type': 'ir.actions.report.xml', 'report_name': 'account.balance.full2', 'datas': data}

fl_account_balance_full_report()

class fl_account_general_ledger_cumulative_report(osv.osv_memory):


    _name = 'fl.account.general.ledger.cumulative.report'
    _columns = {
        'account_list': fields.many2many('account.account', 'general_ledger_cumulative_rel_2', 'ledger_cumulative_id', 'account_id', 'Account'),
        'company_id': fields.many2one('res.company', 'Company'),
        'state': fields.selection((('bydate','By Date'),('byperiod','By Period'),('all','By Date and Period'),('none','No Filter')),'Date/Period Filter'),
        'fiscalyear': fields.many2one('account.fiscalyear', 'Fiscal year', help='Keep empty for all open fiscal year'),
        'periods':fields.many2many('account.period', 'general_ledger_cumulative_period_rel2', 'ledger_cumulative_id','period_id', 'Periods', help='All periods in the fiscal year if empty'),

        'sortbydate':fields.selection((('sort_date','Date'),('sort_mvt','Movement')),'Sort by'),
        'display_account': fields.selection((('bal_mouvement','With movements'),('bal_all','All'),('bal_solde','With balance is not equal to 0')), 'Display accounts'),

        'landscape':fields.boolean('Landscape Mode'),
        'initial_balance':fields.boolean('Show initial balances'),
        'amount_currency':fields.boolean('With Currency'),
        'date_from':fields.date('Start date',required=True),
        'date_to':fields.date('End date',required=True),
        'states': fields.selection((('account_selection','Account Selection'),('checktype','Check Type')), 'State'),



    }

    def _init_states(self, cr, uid, context=None):
        return 'account_selection'

    def step1(self, cr, uid, ids, context):
        data={'states': 'checktype'}
        user=self.pool.get('res.users').browse(cr, uid, uid, context=context)
        if user.company_id:
            company_id = user.company_id.id
        else:
            company_id = self.pool.get('res.company').search(cr, uid, [('parent_id', '=', False)])[0]
        data['company_id']=company_id
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        data['fiscalyear'] = fiscalyear_obj.find(cr, uid)
        self.write(cr, uid, ids, data)
        return True

    def prints(self, cr, uid, ids, context):

        if context is None:
            context = {}
            
        data = {}
        data['ids'] = context.get('active_ids', [])
        data['model'] = context.get('active_model', 'ir.ui.menu')
        data['form'] = self.read(cr, uid, ids[0])
        if data['form']['state'] == 'bydate':
            sql = """SELECT f.id, f.date_start, f.date_stop
                FROM account_fiscalyear f
                WHERE '%s' between f.date_start and f.date_stop """ % (data['form']['date_from'])
            cr.execute(sql)
            res = cr.dictfetchall()
            if res:
                if (data['form']['date_to'] > res[0]['date_stop'] or data['form']['date_to'] < res[0]['date_start']):
                        raise  wizard.except_wizard(_('UserError'),_('Date to must be set between %s and %s') % (str(res[0]['date_start']), str(res[0]['date_stop'])))
            else:
                raise wizard.except_wizard(_('UserError'),_('Date not in a defined fiscal year'))
        if data['form']['landscape']== True:
            return {'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger.cumulative.landscape2', 'datas': data}
        else:
            return {'type': 'ir.actions.report.xml', 'report_name': 'account.general.ledger.cumulative2', 'datas': data}

    _defaults = {
        'date_from': lambda *a: time.strftime('%Y-01-01'),
        'date_to': lambda *a: time.strftime('%Y-%m-%d'),
        'states': lambda self,cr,uid,c: self._init_states(cr, uid, context=c),
        'state' : lambda *a:'none',
    }

fl_account_general_ledger_cumulative_report()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
