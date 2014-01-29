# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Factor Libre.
#    Developer Rafael Valle       
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

import time, dateutil, dateutil.tz
from datetime import date, datetime

import cStringIO
import base64
from xlwt import *
import pooler
from osv import osv, fields
from tools.translate import _
import logging
_logger = logging.getLogger(__name__)

class account_report_general_ledger(osv.osv_memory):
    _inherit = "account.report.general.ledger"

    

    _columns = {
        'name': fields.char('Filename', size=64, readonly=True),
        'export_file': fields.binary('Export File', readonly=True),
    }
    


    def _get_account(self, cr, uid, data):
        if data.get('form', False) and data['form'].get('chart_account_id', False):
            return pooler.get_pool(cr.dbname).get('account.account').browse(cr, uid, data['form']['chart_account_id']).name
        return ''

    
    def _get_fiscalyear(self, cr, uid, data):
        if data.get('form', False) and data['form'].get('fiscalyear_id', False):
            return pooler.get_pool(cr.dbname).get('account.fiscalyear').browse(cr, uid, data['form']['fiscalyear_id']).name
        return ''

    def _get_journal(self, cr, uid, data):
        codes = []
        if data.get('form', False) and data['form'].get('journal_ids', False):
            cr.execute('select code from account_journal where id IN %s',(tuple(data['form']['journal_ids']),))
            codes = ','.join([x for x, in cr.fetchall()])
        return codes

    def _get_target_move(self, cr, uid, data):
        if data.get('form', False) and data['form'].get('target_move', False):
            if data['form']['target_move'] == 'all':
                return _('All Entries')
            return _('All Posted Entries')
        return ''




    def _sum_balance_account(self, cr, uid, account, query, target_move, init_balance):
        if account.type == 'view':
            return account.balance
        move_state = ['draft','posted']
        if target_move == 'posted':
            move_state = ['posted','']
        cr.execute('SELECT (sum(debit) - sum(credit)) as tot_balance \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                AND '+ query +' '
                ,(account.id, tuple(move_state)))
        sum_balance = cr.fetchone()[0] or 0.0
        if init_balance:
            cr.execute('SELECT (sum(debit) - sum(credit)) as tot_balance \
                    FROM account_move_line l \
                    JOIN account_move am ON (am.id = l.move_id) \
                    WHERE (l.account_id = %s) \
                    AND (am.state IN %s) \
                    AND '+ self.init_query +' '
                    ,(account.id, tuple(move_state)))
            # Add initial balance to the result
            sum_balance += cr.fetchone()[0] or 0.0
        return sum_balance


    def _sum_credit_account(self, cr, uid, account, target_move, init_balance, query, init_query):
        if account.type == 'view':
            return account.credit
        move_state = ['draft','posted']
        if target_move == 'posted':
            move_state = ['posted','']
        cr.execute('SELECT sum(credit) \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                AND '+ query +' '
                ,(account.id, tuple(move_state)))
        sum_credit = cr.fetchone()[0] or 0.0
        if init_balance:
            cr.execute('SELECT sum(credit) \
                    FROM account_move_line l \
                    JOIN account_move am ON (am.id = l.move_id) \
                    WHERE (l.account_id = %s) \
                    AND (am.state IN %s) \
                    AND '+ init_query +' '
                    ,(account.id, tuple(move_state)))
            # Add initial balance to the result
            sum_credit += cr.fetchone()[0] or 0.0
        return sum_credit

    def _sum_debit_account(self, cr, uid, account, target_move, init_balance, query, init_query):
        if account.type == 'view':
            return account.debit
        move_state = ['draft','posted']
        if target_move == 'posted':
            move_state = ['posted','']
        cr.execute('SELECT sum(debit) \
                FROM account_move_line l \
                JOIN account_move am ON (am.id = l.move_id) \
                WHERE (l.account_id = %s) \
                AND (am.state IN %s) \
                AND '+ query +' '
                ,(account.id, tuple(move_state)))
        sum_debit = cr.fetchone()[0] or 0.0
        if init_balance:
            cr.execute('SELECT sum(debit) \
                    FROM account_move_line l \
                    JOIN account_move am ON (am.id = l.move_id) \
                    WHERE (l.account_id = %s) \
                    AND (am.state IN %s) \
                    AND '+ init_query +' '
                    ,(account.id, tuple(move_state)))
            # Add initial balance to the result
            sum_debit += cr.fetchone()[0] or 0.0
        return sum_debit

    def get_children_accounts(self, cr, uid, account, data, context):
        res = []
        
        ctx2 = data['form'].get('used_context',{}).copy()
        query = self.pool.get('account.move.line')._query_get(cr, uid, obj='l', context=data['form'].get('used_context',{}))
        sold_accounts = {}
        display_account = data['form']['display_account']        
        target_move = data['form'].get('target_move', 'all')
        init_balance = data['form'].get('initial_balance', True)
        if init_balance:
            ctx2.update({'initial_bal': True})
        init_query = self.pool.get('account.move.line')._query_get(cr, uid, obj='l', context=ctx2)

        account=self.pool.get('account.account').browse(cr,uid,account)
        currency_obj = self.pool.get('res.currency')
        ids_acc = self.pool.get('account.account')._get_children_and_consol(cr, uid, account.id)
        currency = account.currency_id and account.currency_id or account.company_id.currency_id
        for child_account in self.pool.get('account.account').browse(cr, uid, ids_acc, context=context):
            sql = """
                SELECT count(id)
                FROM account_move_line AS l
                WHERE %s AND l.account_id = %%s
            """ % (query)
            cr.execute(sql, (child_account.id,))
            num_entry = cr.fetchone()[0] or 0
            sold_account = self._sum_balance_account(cr, uid, child_account, query, target_move, init_balance)
            sold_accounts[child_account.id] = sold_account
            if display_account == 'movement':
                if child_account.type != 'view' and num_entry <> 0:
                    res.append(child_account)
            elif display_account == 'not_zero':
                if child_account.type != 'view' and num_entry <> 0:
                    if not currency_obj.is_zero(cr, uid, currency, sold_account):
                        res.append(child_account)
            else:
                res.append(child_account)
        if not res:
            return [account]
        return res

    
    
    def _get_period(self, cr, uid, move):
        if move:
            acc_move_ids=self.pool.get('account.move').search(cr, uid, [('name','=',move)])
            if acc_move_ids:
                acc_move_obj=self.pool.get('account.move').browse(cr, uid, acc_move_ids[0])
                if acc_move_obj.period_id:
                    return acc_move_obj.period_id.name
        return ''


    def lines(self, cr, uid, account, sortby, tot_currency, target_move, init_balance, query, init_query):
        """ Return all the account_move_line of account with their account code counterparts """
        move_state = ['draft','posted']
        if target_move == 'posted':
            move_state = ['posted', '']
        # First compute all counterpart strings for every move_id where this account appear.
        # Currently, the counterpart info is used only in landscape mode
        sql = """
            SELECT m1.move_id,
                array_to_string(ARRAY(SELECT DISTINCT a.code
                                          FROM account_move_line m2
                                          LEFT JOIN account_account a ON (m2.account_id=a.id)
                                          WHERE m2.move_id = m1.move_id
                                          AND m2.account_id<>%%s), ', ') AS counterpart
                FROM (SELECT move_id
                        FROM account_move_line l
                        LEFT JOIN account_move am ON (am.id = l.move_id)
                        WHERE am.state IN %s and %s AND l.account_id = %%s GROUP BY move_id) m1
        """% (tuple(move_state), query)
        cr.execute(sql, (account.id, account.id))
        counterpart_res = cr.dictfetchall()
        counterpart_accounts = {}
        for i in counterpart_res:
            counterpart_accounts[i['move_id']] = i['counterpart']
        del counterpart_res

        # Then select all account_move_line of this account
        if sortby == 'sort_journal_partner':
            sql_sort='j.code, p.name, l.move_id'
        else:
            sql_sort='l.date, l.move_id'
        sql = """
            SELECT l.id AS lid, l.date AS ldate, j.code AS lcode, l.currency_id,l.amount_currency,l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit, l.period_id AS lperiod_id, l.partner_id AS lpartner_id,
            m.name AS move_name, m.id AS mmove_id,per.code as period_code,
            c.symbol AS currency_code,
            i.id AS invoice_id, i.type AS invoice_type, i.number AS invoice_number,
            p.name AS partner_name
            FROM account_move_line l
            JOIN account_move m on (l.move_id=m.id)
            LEFT JOIN res_currency c on (l.currency_id=c.id)
            LEFT JOIN res_partner p on (l.partner_id=p.id)
            LEFT JOIN account_invoice i on (m.id =i.move_id)
            LEFT JOIN account_period per on (per.id=l.period_id)
            JOIN account_journal j on (l.journal_id=j.id)
            WHERE %s AND m.state IN %s AND l.account_id = %%s ORDER by %s
        """ %(query, tuple(move_state), sql_sort)
        cr.execute(sql, (account.id,))
        res_lines = cr.dictfetchall()
        res_init = []
        if res_lines and init_balance:
            #FIXME: replace the label of lname with a string translatable
            sql = """
                SELECT 0 AS lid, '' AS ldate, '' AS lcode, COALESCE(SUM(l.amount_currency),0.0) AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, '' AS lperiod_id, '' AS lpartner_id,
                '' AS move_name, '' AS mmove_id, '' AS period_code,
                '' AS currency_code,
                NULL AS currency_id,
                '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,
                '' AS partner_name
                FROM account_move_line l
                LEFT JOIN account_move m on (l.move_id=m.id)
                LEFT JOIN res_currency c on (l.currency_id=c.id)
                LEFT JOIN res_partner p on (l.partner_id=p.id)
                LEFT JOIN account_invoice i on (m.id =i.move_id)
                JOIN account_journal j on (l.journal_id=j.id)
                WHERE %s AND m.state IN %s AND l.account_id = %%s
            """ %(init_query, tuple(move_state))
            cr.execute(sql, (account.id,))
            res_init = cr.dictfetchall()
        res = res_init + res_lines
        account_sum = 0.0
        for l in res:
            l['move'] = l['move_name'] != '/' and l['move_name'] or ('*'+str(l['mmove_id']))
            l['partner'] = l['partner_name'] or ''
            account_sum += l['debit'] - l['credit']
            l['progress'] = account_sum
            l['line_corresp'] = l['mmove_id'] == '' and ' ' or counterpart_accounts[l['mmove_id']].replace(', ',',')
            # Modification of amount Currency
            if l['credit'] > 0:
                if l['amount_currency'] != None:
                    l['amount_currency'] = abs(l['amount_currency']) * -1
            if l['amount_currency'] != None:
                tot_currency = tot_currency + l['amount_currency']
        return res

    def get_report_file_xls(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}

        data=self.check_report(cr, uid, ids, context)

        #vals context
        ctx2 = data['datas']['form'].get('used_context',{}).copy()
        tot_currency = 0.0
        sortby = data['datas']['form'].get('sortby', 'sort_date')
        query = self.pool.get('account.move.line')._query_get(cr, uid, obj='l', context=data['datas']['form'].get('used_context',{}))
        sold_accounts = {}
        display_account = data['datas']['form']['display_account']        
        target_move = data['datas']['form'].get('target_move', 'all')
        init_balance = data['datas']['form'].get('initial_balance', True)
        if init_balance:
            ctx2.update({'initial_bal': True})
        init_query = self.pool.get('account.move.line')._query_get(cr, uid, obj='l', context=ctx2)

        user = self.pool.get('res.users').browse(cr, uid, uid, context = context)
        
        user_tz = dateutil.tz.gettz(user.context_tz)
        utc_tz = dateutil.tz.tzutc()
       

        excel_temp = cStringIO.StringIO()
        w = Workbook(encoding='utf-8', style_compression=2)
        ws = w.add_sheet('Hoja 1')

        #styles
        style_headers1 = XFStyle()
        # font
        font = Font()
        font.bold = True
        style_headers1.font = font
        # borders
        borders = Borders()
        borders.bottom = Borders.DASHED
        style_headers1.borders = borders

        style_bold = XFStyle()
        # font
        font = Font()
        font.bold = True
        style_bold.font = font
        

        # Header definition
        ws.write_merge(0, 0, 0, 11,'LIBRO MAYOR',style=style_headers1)


        #Main Headers
        ws.write(1,0,'Plan Contable', style=style_headers1)
        ws.write(2,0,'Ejercicio Fiscal', style=style_headers1)
        ws.write(3,0,'Diarios', style=style_headers1)
        ws.write(4,0,'Movimientos destino', style=style_headers1)

        ws.write(1,1,self._get_account(cr,uid,data['datas']))
        ws.write(2,1,self._get_fiscalyear(cr,uid,data['datas']))
        ws.write(3,1,self._get_journal(cr,uid,data['datas']))
        ws.write(4,1,self._get_target_move(cr,uid,data['datas']))


        #Table headers
    
        ws.write(6,0,'Fecha', style=style_headers1)
        ws.write(6,1,'Periodo', style=style_headers1)
        ws.write(6,2,'Libro', style=style_headers1)
        ws.write(6,3,'Empresa', style=style_headers1)
        ws.write(6,4,'Ref', style=style_headers1)
        ws.write(6,5,'Asiento', style=style_headers1)
        ws.write(6,6,'Etiqueta Asiento', style=style_headers1)
        ws.write(6,7,'Contrapartida', style=style_headers1)
        ws.write(6,8,'Debe', style=style_headers1)
        ws.write(6,9,'Haber', style=style_headers1)
        ws.write(6,10,'Saldo Pendiente', style=style_headers1)
        ws.write(6,11,'Divisa', style=style_headers1)

        row=7
        #Children accounts
        for a in self.get_children_accounts(cr, uid, data['datas']['form']['chart_account_id'],data['datas'], context):
            ws.write(row,0,a.code+' '+a.name, style=style_bold)
            ws.write(row,8,self._sum_debit_account(cr, uid, a, target_move, init_balance, query, init_query), style=style_bold)
            ws.write(row,9,self._sum_credit_account(cr, uid, a, target_move, init_balance, query, init_query), style=style_bold)
            #ws.write(row,10,self._sum_balance_account(cr, uid, a, query, target_move, init_balance))       
            row=row+1
            
            #lines children
            for a_line in self.lines(cr, uid, a, sortby, tot_currency, target_move, init_balance, query, init_query):

                #format date
                ldated=datetime.strptime(a_line['ldate'], '%Y-%m-%d')

                ws.write(row,0,ldated.strftime('%d/%m/%Y'))
                ws.write(row,1,self._get_period(cr, uid, a_line['move']))
                ws.write(row,2,a_line['lcode'])
                ws.write(row,3,a_line['partner_name'])
                ws.write(row,4,a_line['lref'])
                ws.write(row,5,a_line['move'])
                ws.write(row,6,a_line['lname'])
                ws.write(row,7,a_line['line_corresp'])
                ws.write(row,8,a_line['debit'])
                ws.write(row,9,a_line['credit'])
                ws.write(row,10,a_line['progress'])
                ws.write(row,11,a_line['currency_code'] or '')
                row=row+1

        w.save(excel_temp)
        out=base64.encodestring(excel_temp.getvalue())
        excel_temp.close()
        file_time = datetime.now(user_tz).strftime('%Y-%m-%d_%H%M')


        return self.write(cr, uid, ids, {'state': 'export', 'export_file': out, 'name': 'Libro_Mayor_%s.xls' % (file_time)})

account_report_general_ledger()

