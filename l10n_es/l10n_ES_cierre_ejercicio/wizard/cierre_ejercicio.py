# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import wizard
import pooler
from osv import osv
from tools import config
from tools.translate import _
import threading

_transaction_form = '''<?xml version="1.0"?>        
<form string="Financial closure">
    <field name="ejercicio_cierre_id"/>
    <field name="ejercicio_apertura_id"/>
    <newline/>
    <separator string="Loss &amp; Profit entry" colspan="4"/>
    <field name="asiento_pyg"/>
    <field name="desc_asiento_pyg" attrs="{'required':[('asiento_pyg','==',True)]}"/>
    <field name="diario_pyg" attrs="{'required':[('asiento_pyg','==',True)]}"/>
    <field name="periodo_pyg_id" attrs="{'required':[('asiento_pyg','==',True)]}"/>
    <separator string="Opening and Closing entries" colspan="4"/>
    <field name="desc_asiento_cierre"/>
    <field name="desc_asiento_apertura"/>
    <field name="diario_cierre"/>
    <field name="diario_apertura"/>
    <field name="periodo_cierre_id"/>
    <field name="periodo_apertura_id"/>
    <separator string="Fiscal year closing confirmation" colspan="4"/>
    <field name="sure"/>
</form>'''

_transaction_fields = {
    'ejercicio_cierre_id': {'string':'Fical year to close', 'type':'many2one', 'relation': 'account.fiscalyear','required':True, 'domain':[('state','=','draft')]},
    'ejercicio_apertura_id': {'string':'Fiscal year to open', 'type':'many2one', 'relation': 'account.fiscalyear', 'domain':[('state','=','draft')], 'required':True},
    'asiento_pyg': {'string':'Create Loss & Profit entry', 'type':'boolean', 'required':True, 'default': lambda *a:True},
    'desc_asiento_pyg': {'string':'Loss & Profit entry description', 'type':'char', 'size': 64},
    'diario_pyg': {'string':'Loss & Profit entry journal', 'type':'many2one', 'relation': 'account.journal'},
    'periodo_pyg_id': {'string': 'Loss & Profit period', 'type': 'many2one', 'relation':'account.period', 'domain':[('state','=','draft'),('special','=',True)]},
    'desc_asiento_cierre': {'string':'Closing entry description', 'type':'char', 'size': 64, 'required':True},
    'desc_asiento_apertura': {'string':'Opening entry description', 'type':'char', 'size': 64, 'required':True},
    'diario_cierre': {'string':'Closing journal', 'type':'many2one', 'relation': 'account.journal', 'required':True},
    'diario_apertura': {'string':'Opening journal', 'type':'many2one', 'relation': 'account.journal', 'required':True},
    'periodo_cierre_id': {'string': 'Closing period', 'type': 'many2one', 'relation':'account.period', 'required': True, 'domain':[('state','=','draft'),('special','=',True)]},
    'periodo_apertura_id': {'string': 'Opening period', 'type': 'many2one', 'relation':'account.period', 'required': True, 'domain':[('state','=','draft'),('special','=',True)]},
    'sure': {'string':'Check this box if you are sure', 'type':'boolean'},
}


class wiz_journal_close(wizard.interface):

    def _data_load(self, cr, uid, data, context):
        data['form']['asiento_pyg'] = True
        data['form']['desc_asiento_pyg'] = _('Loss and Profit entry')
        data['form']['desc_asiento_cierre'] = _('Closing entry')
        data['form']['desc_asiento_apertura'] = _('Opening entry')
        return data['form']


    def _data_save(self, cr, uid, data, context):
        if not data['form']['sure']:
            raise wizard.except_wizard(_('UserError'), _('If you are sure you want to close the fiscal year, check the box'))
        if data['form']['asiento_pyg']:
            self._asiento_pyg(cr, uid, data, context)
        self._procedure_cierre(cr, uid, data, context)
        return {}


    def _asiento_pyg(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        period_id = data['form']['periodo_pyg_id']
        journal_id = data['form']['diario_pyg']
        period = pool.get('account.period').browse(cr, uid, period_id, context=context)
        journal = pool.get('account.journal').browse(cr, uid, journal_id, context=context)

        if not journal.default_credit_account_id or not journal.default_debit_account_id:
            raise wizard.except_wizard(_('UserError'),
                    _('The journal for Loss and Profit entry must have default credit and debit account'))
        if not journal.centralisation:
            raise wizard.except_wizard(_('UserError'),
                    _('The journal for Loss and Profit entry must have centralised counterpart'))

        move_ids = pool.get('account.move.line').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if move_ids:
            raise wizard.except_wizard(_('UserError'),
                    _('The journal and period for Loss and Profit entry must not have any previous entry!'))

        acc_type_ids = pool.get('account.account.type').search(cr, uid, [('code','in',['ingresos','gastos'])])
        acc_type = ','.join(map(str, acc_type_ids))
        cr.execute("SELECT id FROM account_account WHERE type <> 'view' AND user_type in (%s)" % acc_type)
        acc_ids = map(lambda x: x[0], cr.fetchall())
        context['fiscalyear'] = data['form']['ejercicio_cierre_id']
        for account in pool.get('account.account').browse(cr, uid, acc_ids, context):
            if abs(account.balance) > 10**-int(config['price_accuracy']):
                linea =  {
                    'debit': account.balance<0 and -account.balance,
                    'credit': account.balance>0 and account.balance,
                    'name': data['form']['desc_asiento_pyg'],
                    'date': period.date_stop,
                    'journal_id': journal_id,
                    'period_id': period_id,
                    'account_id': account.id
                    }
                pool.get('account.move.line').create(cr, uid, linea, {'journal_id': journal_id, 'period_id':period_id})

        ids = pool.get('account.move.line').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if ids:
            move_line = pool.get('account.move.line').browse(cr, uid, ids[0])
            pool.get('account.move').write(cr, uid, [move_line.move_id.id], {'name': data['form']['desc_asiento_pyg']})
            pool.get('account.move').button_validate(cr, uid, [move_line.move_id.id], context)
            print "ID Loss and Profit entry: " + str(move_line.move_id.id)
        return {}


    def revert_move(self, cr, uid, data, move_id, journal_id, period_id, date, reconcile=True, context={}):
        pool = pooler.get_pool(cr.dbname)
        journal = pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        move_obj = pool.get('account.move')
        move = move_obj.browse(cr, uid, move_id, context)
        for line in move.line_id:
            if line.account_id == journal.default_credit_account_id or line.account_id == journal.default_debit_account_id:
                continue
            linea =  {
                'debit': line.credit,
                'credit': line.debit,
                'name': line.name == data['form']['desc_asiento_cierre'] and data['form']['desc_asiento_apertura'] or line.name,
                'journal_id': journal_id,
                'period_id': period_id,
                'account_id': line.account_id.id
                }
            if date:
                linea['date'] = date,
            pool.get('account.move.line').create(cr, uid, linea, {'journal_id': journal_id, 'period_id':period_id})

        ids = pool.get('account.move.line').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if ids:
            move_line = pool.get('account.move.line').browse(cr, uid, ids[0])
            copy_id = move_line.move_id.id
            move_obj.write(cr, uid, [copy_id], {'name': data['form']['desc_asiento_apertura']})
        else:
            return False

        if reconcile:
            reconcile_lines = pool.get('account.move.line').search(cr, uid, [('account_id.reconcile','=','True'),('move_id','in',[move_id, copy_id])])
            r_id = pool.get('account.move.reconcile').create(cr, uid, {
                'type': 'manual',
                'line_id': map(lambda x: (4,x,False), reconcile_lines)})
        print "Revert entry (opening entry) done"
        return copy_id


    def _asiento_cierre(self, db_name, uid, data, context):
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()
        pool = pooler.get_pool(cr.dbname)
        fy_id = data['form']['ejercicio_cierre_id']
        period_ids = pool.get('account.period').search(cr, uid, [('fiscalyear_id', '=', fy_id)])
        fy_period_set = ','.join(map(str, period_ids))
        fy2_id = data['form']['ejercicio_apertura_id']
        periods_fy2 = pool.get('account.period').search(cr, uid, [('fiscalyear_id', '=', fy2_id)])
        fy2_period_set = ','.join(map(str, periods_fy2))

        old_fyear = pool.get('account.fiscalyear').browse(cr, uid, fy_id, context=context)
        new_fyear = pool.get('account.fiscalyear').browse(cr, uid, fy2_id, context=context)

        period_id = data['form']['periodo_cierre_id']
        journal_id = data['form']['diario_cierre']
        period = pool.get('account.period').browse(cr, uid, period_id, context=context)
        journal = pool.get('account.journal').browse(cr, uid, journal_id, context=context)

        query_line = pool.get('account.move.line')._query_get(cr, uid,
                obj='account_move_line', context={'fiscalyear': fy_id})
        cr.execute('select id from account_account WHERE active')
        ids = map(lambda x: x[0], cr.fetchall())
        for account in pool.get('account.account').browse(cr, uid, ids,
            context={'fiscalyear': fy_id}):
            
            accnt_type_data = account.user_type
            if not accnt_type_data:
                continue
            if accnt_type_data.close_method=='none' or account.type == 'view':
                continue
            if accnt_type_data.close_method=='balance':
                if abs(account.balance) > 10**-int(config['price_accuracy']):
                    pool.get('account.move.line').create(cr, uid, {
                        'debit': account.balance>0 and account.balance,
                        'credit': account.balance<0 and -account.balance,
                        'name': data['form']['desc_asiento_cierre'],
                        'date': period.date_start,
                        'journal_id': journal_id,
                        'period_id': period_id,
                        'account_id': account.id
                    }, {'journal_id': journal_id, 'period_id':period_id})
            if accnt_type_data.close_method == 'unreconciled':
                offset = 0
                limit = 100
                while True:
                    cr.execute('SELECT id, name, quantity, debit, credit, account_id, ref, ' \
                                'amount_currency, currency_id, blocked, partner_id, ' \
                                'date_maturity, date_created ' \
                            'FROM account_move_line ' \
                            'WHERE account_id = %s ' \
                                'AND ' + query_line + ' ' \
                                'AND reconcile_id is NULL ' \
                            'ORDER BY id ' \
                            'LIMIT %s OFFSET %s', (account.id, limit, offset))
                    result = cr.dictfetchall()
                    if not result:
                        break
                    for move in result:
                        move.pop('id')
                        move.update({
                            'date': period.date_start,
                            'journal_id': journal_id,
                            'period_id': period_id,
                        })
                        pool.get('account.move.line').create(cr, uid, move, {
                            'journal_id': journal_id,
                            'period_id': period_id,
                            })
                    offset += limit

                #We have also to consider all move_lines that were reconciled 
                #on another fiscal year, and report them too
                offset = 0
                limit = 100
                while True:
                    #TODO: this query could be improved in order to work if there is more than 2 open FY
                    # a.period_id IN ('+fy2_period_set+') is the problematic clause
                    cr.execute('SELECT b.id, b.name, b.quantity, b.debit, b.credit, b.account_id, b.ref, ' \
                                'b.amount_currency, b.currency_id, b.blocked, b.partner_id, ' \
                                'b.date_maturity, b.date_created ' \
                            'FROM account_move_line a, account_move_line b ' \
                            'WHERE b.account_id = %s ' \
                                'AND b.reconcile_id is NOT NULL ' \
                                'AND a.reconcile_id = b.reconcile_id ' \
                                'AND b.period_id IN ('+fy_period_set+') ' \
                                'AND a.period_id IN ('+fy2_period_set+') ' \
                            'ORDER BY id ' \
                            'LIMIT %s OFFSET %s', (account.id, limit, offset))
                    result = cr.dictfetchall()
                    if not result:
                        break
                    for move in result:
                        move.pop('id')
                        move.update({
                            'date': period.date_start,
                            'journal_id': journal_id,
                            'period_id': period_id,
                        })
                        pool.get('account.move.line').create(cr, uid, move, {
                            'journal_id': journal_id,
                            'period_id': period_id,
                            })
                    offset += limit
            if accnt_type_data.close_method=='detail':
                offset = 0
                limit = 100
                while True:
                    cr.execute('SELECT id, name, quantity, debit, credit, account_id, ref, ' \
                                'amount_currency, currency_id, blocked, partner_id, ' \
                                'date_maturity, date_created ' \
                            'FROM account_move_line ' \
                            'WHERE account_id = %s ' \
                                'AND ' + query_line + ' ' \
                            'ORDER BY id ' \
                            'LIMIT %s OFFSET %s', (account.id, limit, offset))
                    
                    result = cr.dictfetchall()
                    if not result:
                        break
                    for move in result:
                        move.pop('id')
                        move.update({
                            'date': period.date_start,
                            'journal_id': journal_id,
                            'period_id': period_id,
                        })
                        pool.get('account.move.line').create(cr, uid, move)
                    offset += limit
        ids = pool.get('account.move.line').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if ids:
            context['fy_closing'] = True
            #pool.get('account.move.line').reconcile(cr, uid, ids, context=context)
            move_line = pool.get('account.move.line').browse(cr, uid, ids[0])
            cierre_id = move_line.move_id.id
            pool.get('account.move').write(cr, uid, [cierre_id], {'name': data['form']['desc_asiento_cierre']})
            print "ID closing entry: " + str(cierre_id)
        else:
            return {}

        ids = pool.get('account.journal.period').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if not ids:
            ids = [pool.get('account.journal.period').create(cr, uid, {
                   'name': (journal.name or '')+':'+(period.code or ''),
                   'journal_id': journal_id,
                   'period_id': period_id
               })]
        cr.execute('UPDATE account_fiscalyear ' \
                    'SET end_journal_period_id = %s ' \
                    'WHERE id = %s', (ids[0], old_fyear.id))

        apertura_id = self.revert_move(cr, uid, data, cierre_id, data['form']['diario_apertura'], data['form']['periodo_apertura_id'], pool.get('account.period').browse(cr,uid,data['form']['periodo_apertura_id']).date_start, True, context)
        print "ID opening entry: " + str(apertura_id)
        pool.get('account.move').button_validate(cr, uid, [cierre_id, apertura_id], context)

        result = cr.commit()
        return {}


    def _procedure_cierre(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)

        period_id = data['form']['periodo_cierre_id']
        journal_id = data['form']['diario_cierre']
        journal = pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        
        if not journal.default_credit_account_id or not journal.default_debit_account_id:
            raise osv.except_osv(_('UserError'),
                    _('The journal for Closing entry must have default credit and debit account'))
        if not journal.centralisation:
            raise osv.except_osv(_('UserError'),
                    _('The journal for Closing entry must have centralised counterpart'))
        move_ids = pool.get('account.move.line').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if move_ids:
            raise osv.except_osv(_('UserError'),
                    _('The journal and period for Closing entry must not have any previous entry!'))

        period_id = data['form']['periodo_apertura_id']
        journal_id = data['form']['diario_apertura']
        journal = pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        
        if not journal.default_credit_account_id or not journal.default_debit_account_id:
            raise osv.except_osv(_('UserError'),
                    _('The journal for Opening entry must have default credit and debit account'))
        if not journal.centralisation:
            raise osv.except_osv(_('UserError'),
                    _('The journal for Opening entry must have centralised counterpart'))
        move_ids = pool.get('account.move.line').search(cr, uid, [('journal_id','=',journal_id),('period_id','=',period_id)])
        if move_ids:
            raise osv.except_osv(_('UserError'),
                    _('The journal and period for Opening entry must not have any previous entry!'))

        if data['form']['periodo_cierre_id'] == data['form']['periodo_apertura_id'] or (data['form']['asiento_pyg'] and data['form']['periodo_cierre_id'] == data['form']['periodo_pyg_id']):
            raise osv.except_osv(_('UserError'),
                    _('The Closing, Opening and Loss and Profit periods must be different!'))

        threaded_calculation = threading.Thread(target=self._asiento_cierre, args=(cr.dbname, uid, data, context))
        threaded_calculation.start()
        return {}


    states = {
        'init': {
            'actions': [_data_load],
            'result': {'type': 'form', 'arch':_transaction_form, 'fields':_transaction_fields, 'state':[('end','Cancel'),('close','Close fiscal year')]}
        },
        'close': {
            'actions': [_data_save],
            'result': {'type': 'state', 'state':'end'}
        }
    }
wiz_journal_close('l10n_ES.fiscalyear.close')

