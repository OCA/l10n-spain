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

class fl_account_general_ledger_cumulative_report(osv.osv_memory):
    _inherit = "fl.account.general.ledger.cumulative.report"

    

    _columns = {
        'name': fields.char('Filename', size=64, readonly=True),
        'export_file': fields.binary('Export File', readonly=True),
    }
    


    

    
    def get_fiscalyear(self, cr, uid, form):
        res=[]
        if form.has_key('fiscalyear'):
            fisc_id = form['fiscalyear']
            if not (fisc_id):
                return ''
            cr.execute("SELECT name FROM account_fiscalyear WHERE id = %s" , (int(fisc_id),))
            res=cr.fetchone()
        return res and res[0] or ''

    
    def get_periods(self, cr, uid, form):
        result=''
        if form.has_key('periods') and form['periods']:
            period_ids = ",".join([str(x) for x in form['periods'] if x])
            cr.execute("SELECT name FROM account_period WHERE id in (%s)" % (period_ids))
            res = cr.fetchall()
            len_res = len(res) 
            for r in res:
                if (r == res[len_res-1]):
                    result+=r[0]+". "
                else:
                    result+=r[0]+", "
        elif form.has_key('date_from') and form.has_key('date_to'):
            result = form['date_from'] + ' - ' + form['date_to'] + ' '
        else:
            fy_obj = self.pool.get('account.fiscalyear').browse(cr,uid,form['fiscalyear'])
            res = fy_obj.period_ids
            len_res = len(res)
            for r in res:
                if r == res[len_res-1]:
                    result+=r.name+". "
                else:
                    result+=r.name+", "
            
        return str(result and result[:-1]) or ''



    def _sum_balance_account(self, cr, uid, account, form, ctxfy):
        # Balance from init fiscal year to last date given by the user
        accounts = self.pool.get('account.account').read(cr, uid, [account.id], ['balance'], ctxfy)
        sum_balance = accounts[0]['balance']
        return sum_balance


    def _sum_debit_account(self, cr, uid, account, form, query):
        cr.execute("SELECT sum(debit) "\
                "FROM account_move_line l "\
                "WHERE l.account_id = %s AND %s " % (account.id, query))
        sum_debit = cr.fetchone()[0] or 0.0
        return sum_debit


    def _sum_credit_account(self, cr, uid, account, form, query):
        cr.execute("SELECT sum(credit) "\
                "FROM account_move_line l "\
                "WHERE l.account_id = %s AND %s " % (account.id, query))
        sum_credit = cr.fetchone()[0] or 0.0
        return sum_credit

    
    def _calc_contrepartie(self, cr, uid, ids, context={}):
        result = {}
        #for id in ids:
        #    result.setdefault(id, False)
        for account_line in self.pool.get('account.move.line').browse(cr, uid, ids, context):
            # For avoid long text in the field we will limit it to 5 lines
            #
            result[account_line.id] = ' '
            num_id_move = str(account_line.move_id.id)
            num_id_line = str(account_line.id)
            account_id = str(account_line.account_id.id)
            # search the basic account
            # We have the account ID we will search all account move line from now until this time
            # We are in the case of we are on the top of the account move Line
            cr.execute("SELECT distinct(ac.code) as code_rest,ac.name as name_rest "\
                "FROM account_account AS ac, account_move_line mv "\
                "WHERE ac.id = mv.account_id and mv.move_id = " + num_id_move + " and mv.account_id <> " + account_id )
            res_mv = cr.dictfetchall()
            # we need a result more than 2 line to make the test so we will made the the on 1 because we have exclude the current line
            if (len(res_mv) >=1):
                concat = ''
                rup_id = 0
                for move_rest in res_mv:
                    concat = concat + move_rest['code_rest'] + '|'
                    result[account_line.id] = concat
                    if rup_id >5:
                        # we need to stop the computing and to escape but before we will add "..."
                        result[account_line.id] = concat + '...'
                        break
                    rup_id+=1
        return result

    def get_children_accounts(self, cr, uid, account, form, query, ctx, context=None):
        balance_accounts = {}
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')
        child_ids = account_obj.search(cr, uid, [('parent_id', 'child_of', form['account_list'])])
        res = []
        ctx = ctx.copy()
        if account and account.child_consol_ids: # add ids of consolidated childs also of selected account
            ctx['consolidate_childs'] = True
            ctx['account_id'] = account.id
        ids_acc = account_obj.search(cr, uid,[('parent_id', 'child_of', [account.id])], context=ctx)
        for child_id in ids_acc:
            child_account = account_obj.browse(cr, uid, child_id)
            balance_account = self._sum_balance_account( cr, uid, child_account, form, {})
            balance_accounts[child_account.id] = balance_account
            if form['display_account'] == 'bal_mouvement':
                if child_account.type != 'view' \
                and len(move_line_obj.search(cr, uid,
                    [('account_id','=',child_account.id)],
                    context=ctx)) <> 0 :
                    res.append(child_account)
            elif form['display_account'] == 'bal_solde':
                if child_account.type != 'view' \
                and len(move_line_obj.search(cr, uid,
                    [('account_id','=',child_account.id)],
                    context=ctx)) <> 0 :
                    if balance_account <> 0.0:
                        res.append(child_account)
            else:
                if child_account.type != 'view' \
                and len(move_line_obj.search(cr, uid,
                    [('account_id','>=',child_account.id)],
                    context=ctx)) <> 0 :
                    res.append(child_account)
        ##
        if not len(res):
            return [account]
        else:
            ## We will now compute initial balance
            for move in res:
                sql_balance_init = "SELECT sum(l.debit) AS sum_debit, sum(l.credit) AS sum_credit "\
                    "FROM account_move_line l "\
                    "WHERE l.account_id = " + str(move.id) +  " AND %s" % (query)
                cr.execute(sql_balance_init)
                resultat = cr.dictfetchall()
                if resultat[0] :
                    if resultat[0]['sum_debit'] == None:
                        sum_debit = 0
                    else:
                        sum_debit = resultat[0]['sum_debit']
                    if resultat[0]['sum_credit'] == None:
                        sum_credit = 0
                    else:
                        sum_credit = resultat[0]['sum_credit']

                    move.init_credit = sum_credit
                    move.init_debit = sum_debit
                else:
                    move.init_credit = 0
                    move.init_debit = 0
        return res



    def lines(self, cr, uid, account, form, query, ctxfy):
        tot_currency = 0.0
        date_min = period_min = False
        date_min = form['date_from']

        #dates
        if not period_min:
            min_date = date_min
        elif not date_min:
            min_date = period_min
        else:
            # If period and date are given, the maximum of the min dates is choosed
            if period_min < date_min:
                min_date = date_min
            else:
                min_date = period_min        




        print query
        inv_types = {
                'out_invoice': _('CI: '),
                'in_invoice': _('SI: '),
                'out_refund': _('OR: '),
                'in_refund': _('SR: '),
                }

        if form['sortbydate'] == 'sort_date':
            sorttag = 'l.date'
        else:
            sorttag = 'j.code'
        sql = """
            SELECT l.id, l.date, j.code, c.symbol AS currency_code, l.amount_currency, l.ref, l.name , l.debit, l.credit, l.period_id
                    FROM account_move_line as l
                       LEFT JOIN res_currency c on (l.currency_id=c.id)
                          JOIN account_journal j on (l.journal_id=j.id)
                             AND account_id = %%s
                             AND %s
                               ORDER by %s""" % (query, sorttag)
        cr.execute(sql % account.id)

        res = cr.dictfetchall()
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')

        # Balance from init fiscal year to last date given by the user
        accounts = account_obj.read(cr, uid, [account.id], ['balance'], ctxfy)
        sum = accounts[0]['balance']

        for l in reversed(res):
            line = move_line_obj.browse(cr, uid, l['id'])
            l['move'] = line.move_id.name_split
            cr.execute('Select id from account_invoice where move_id =%s'%(line.move_id.id))
            tmpres = cr.dictfetchall()
            if len(tmpres) > 0 :
                inv = invoice_obj.browse(cr, uid, tmpres[0]['id'])
                l['ref'] = inv_types[inv.type] + ': '+str(inv.number)
            if line.partner_id :
                l['partner'] = line.partner_id.name
            else :
                l['partner'] = ''
            l['line_corresp'] = self._calc_contrepartie(cr,uid,[l['id']])[l['id']]

            # Cumulative balance update
            l['progress'] = sum
            sum = sum - l['debit'] + l ['credit']

            # Modification of currency amount
            if (l['credit'] > 0):
                if l['amount_currency'] != None:
                    l['amount_currency'] = abs(l['amount_currency']) * -1
            if l['amount_currency'] != None:
                tot_currency = tot_currency + l['amount_currency']

        decimal_precision_obj = self.pool.get('decimal.precision')
        ids = decimal_precision_obj.search(cr, uid, [('name', '=', 'Account')])
        digits = decimal_precision_obj.browse(cr, uid, ids)[0].digits

        #if abs(sum) > 10**-int(config['price_accuracy']) and form['initial_balance']:
        if round(sum,digits) <> 0.0  and form['initial_balance']:
            res.insert(0, {
                'date': self.min_date,
                'name': _('Initial balance'),
                'progress': sum,
                'partner': '',
                'move': '',
                'ref': '',
                'debit': '',
                'credit': '',
                'amount_currency': '',
                'currency_code': '',
                'code': '',
                'line_corresp': '',
            })

        return res


    

    def get_report_file_xls(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}

        data=self.prints(cr, uid, ids, context)
        print data


        #vals context
        ctx2 = data['datas']['form'].get('used_context',{}).copy()
        tot_currency = 0.0
        sortby = data['datas']['form'].get('sortby', 'sort_date')

        ctx = context.copy()
        if 'fiscalyear' in data['datas']['form'] and data['datas']['form']['fiscalyear']:
            ctx['fiscalyear'] = data['datas']['form']['fiscalyear']
        if data['datas']['form']['state'] in ['byperiod', 'all']:
            ctx['periods'] = data['datas']['form']['periods']
        if data['datas']['form']['state'] in ['bydate', 'all']:
            ctx['date_from'] = data['datas']['form']['date_from']
            ctx['date_to'] = data['datas']['form']['date_to']
        if 'periods' not in ctx:
            ctx['periods'] = []
            ctx = ctx
        
        ctxfy = ctx.copy()
        ctxfy['periods'] = ctx['periods'][:]

        #-----------------------------------------

        query = self.pool.get('account.move.line')._query_get(cr, uid, context=ctx)

        
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
        ws.write_merge(0, 0, 0, 11,'LIBRO MAYOR ACUMULADO',style=style_headers1)


        #Main Headers
        ws.write(1,0,'Año Fiscal', style=style_headers1)
        ws.write(2,0,'Periodos', style=style_headers1)


        
        ws.write(1,1,self.get_fiscalyear(cr,uid,data['datas']['form']))
        ws.write(2,1,self.get_periods(cr,uid,data['datas']['form']))


        #Table headers
    
        ws.write(6,0,'Fecha', style=style_headers1)
        ws.write(6,1,'Asiento', style=style_headers1)
        ws.write(6,2,'Empresa', style=style_headers1)
        ws.write(6,3,'Ref', style=style_headers1)
        ws.write(6,4,'Debe', style=style_headers1)
        ws.write(6,5,'Haber', style=style_headers1)
        ws.write(6,6,'Balance', style=style_headers1)


        row=7
        #Children accounts

        for account_id in data['datas']['form']['account_list']:
            acc_obj=self.pool.get('account.account').browse(cr,uid,account_id)
            for a in self.get_children_accounts(cr, uid, acc_obj, data['datas']['form'], query, ctx, context):
                ws.write(row,0,a.code+' '+a.name, style=style_bold)
                ws.write(row,4,self._sum_debit_account(cr, uid, a, data['datas']['form'], query), style=style_bold)
                ws.write(row,5,self._sum_credit_account(cr, uid, a, data['datas']['form'], query), style=style_bold)
                ws.write(row,6,self._sum_balance_account( cr, uid, a, data['datas']['form'], ctxfy), style=style_bold) 
                row=row+1
                
                #lines children
                for a_line in self.lines(cr, uid, a, data['datas']['form'], query, ctxfy):

                    #format date
                    ldated=datetime.strptime(a_line['date'], '%Y-%m-%d')

                    ws.write(row,0,ldated.strftime('%d/%m/%Y'))
                    ws.write(row,1,a_line['move'])
                    ws.write(row,2,a_line['partner'])
                    ws.write(row,3,a_line['ref'])
                    ws.write(row,4,a_line['debit'])
                    ws.write(row,5,a_line['credit'])
                    ws.write(row,6,a_line['progress'])
                    row=row+1

        w.save(excel_temp)
        out=base64.encodestring(excel_temp.getvalue())
        excel_temp.close()
        file_time = datetime.now(user_tz).strftime('%Y-%m-%d_%H%M')


        return self.write(cr, uid, ids, { 'export_file': out, 'name': 'Libro_Mayor_Acumulado_%s.xls' % (file_time)})

fl_account_general_ledger_cumulative_report()

