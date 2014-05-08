# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2005-2006 CamptoCamp
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import time
from report import report_sxw
from tools import config
from tools.translate import _
import rml_parse

class general_ledger(rml_parse.rml_parse):
    _name = 'report.account.general.ledger.cumulative2'

    def set_context(self, objects, data, ids, report_type = None):
        self.get_context_date_period(data['form'])
        new_ids = []
        if (data['model'] == 'account.account'):
            new_ids = ids
        else:
            new_ids = data['form']['account_list']
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        super(general_ledger, self).set_context(objects, data, new_ids, report_type)


    def __init__(self, cr, uid, name, context):
        super(general_ledger, self).__init__(cr, uid, name, context=context)
        self.query = ""    # SQL query to get account moves for given date or period
        self.min_date = "" # Min date of the given date or period
        self.ctx = {}      # Context for given date or period
        self.ctxfy = {}    # Context from the date start or first period of the fiscal year
        self.child_ids = ""
        self.tot_currency = 0.0
        self.balance_accounts = {}
        self.localcontext.update( {
            'time': time,
            'lines': self.lines,
            'sum_debit_account': self._sum_debit_account,
            'sum_credit_account': self._sum_credit_account,
            'sum_balance_account': self._sum_balance_account,
            'get_children_accounts': self.get_children_accounts,
            'sum_currency_amount_account': self._sum_currency_amount_account,
            'get_fiscalyear':self.get_fiscalyear,
            'get_periods':self.get_periods,
        })
        self.context = context


    def get_fiscalyear(self, form):
        res=[]
        if 'fiscalyear' in form:
            if isinstance(form['fiscalyear'], int):
                fisc_id = form['fiscalyear']
            else:
                fisc_id = form['fiscalyear'][0]
            if not (fisc_id):
                return ''
            self.cr.execute("SELECT name FROM account_fiscalyear WHERE id = %s" , (int(fisc_id),))
            res=self.cr.fetchone()
        return res and res[0] or ''


    def get_periods(self, form):
        result=''
        if form.has_key('periods') and form['periods']:
            period_ids = ",".join([str(x) for x in form['periods'] if x])
            self.cr.execute("SELECT name FROM account_period WHERE id in (%s)" % (period_ids))
            res = self.cr.fetchall()
            len_res = len(res) 
            for r in res:
                if (r == res[len_res-1]):
                    result+=r[0]+". "
                else:
                    result+=r[0]+", "
        elif form.has_key('date_from') and form.has_key('date_to'):
            result = self.formatLang(form['date_from'], date=True) + ' - ' + self.formatLang(form['date_to'], date=True) + ' '
        else:
            fy_obj = self.pool.get('account.fiscalyear').browse(self.cr,self.uid,form['fiscalyear'][0])
            res = fy_obj.period_ids
            len_res = len(res)
            for r in res:
                if r == res[len_res-1]:
                    result+=r.name+". "
                else:
                    result+=r.name+", "
            
        return str(result and result[:-1]) or ''


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


    def get_context_date_period(self, form):
        date_min = period_min = False

        # ctx: Context for the given date or period
        ctx = self.context.copy()
        if 'fiscalyear' in form and form['fiscalyear']:
            if isinstance(form['fiscalyear'], int):
                ctx['fiscalyear'] = form['fiscalyear']
            else:
                ctx['fiscalyear'] = form['fiscalyear'][0]
        if form['state'] in ['byperiod', 'all']:
            ctx['periods'] = form['periods']
        if form['state'] in ['bydate', 'all']:
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = form['date_to']
        if 'periods' not in ctx:
            ctx['periods'] = []
        self.ctx = ctx
        print ctx
        self.query = self.pool.get('account.move.line')._query_get(self.cr, self.uid, context=ctx)
        # ctxfy: Context from the date start / first period of the fiscal year
        ctxfy = ctx.copy()
        ctxfy['periods'] = ctx['periods'][:]

        if form['state'] in ['byperiod', 'all'] and len(ctx['periods']):
            self.cr.execute("""SELECT id, date_start, fiscalyear_id
                FROM account_period
                WHERE date_start = (SELECT min(date_start) FROM account_period WHERE id in (%s))"""
                % (','.join([str(x) for x in ctx['periods']])))
            res = self.cr.dictfetchone()
            period_min = res['date_start']
            self.cr.execute("""SELECT id
                FROM account_period
                WHERE fiscalyear_id in (%s) AND date_start < '%s'"""
                % (res['fiscalyear_id'], res['date_start']))
            ids = filter(None, map(lambda x:x[0], self.cr.fetchall()))
            ctxfy['periods'].extend(ids)

        if form['state'] in ['bydate', 'all']:
            self.cr.execute("""SELECT date_start
                FROM account_fiscalyear
                WHERE '%s' BETWEEN date_start AND date_stop""" % (ctx['date_from']))
            res = self.cr.dictfetchone()
            ctxfy['date_from'] = res['date_start']
            date_min = form['date_from']

        if form['state'] == 'none' or (form['state'] == 'byperiod' and not len(ctx['periods'])):
            if 'fiscalyear' in form and form['fiscalyear']:
                sql = """SELECT id, date_start
                    FROM account_period
                    WHERE fiscalyear_id in (%s)
                    ORDER BY date_start""" % (ctx['fiscalyear'])
            else:
                sql = """SELECT id, date_start
                    FROM account_period
                    WHERE fiscalyear_id in (SELECT id FROM account_fiscalyear WHERE state='draft')
                    ORDER BY date_start"""
            self.cr.execute(sql)
            res = self.cr.dictfetchall()
            period_min = res[0]['date_start']
            ids = filter(None, map(lambda x:x['id'], res))
            ctxfy['periods'] = ids
        self.ctxfy = ctxfy

        if not period_min:
            self.min_date = date_min
        elif not date_min:
            self.min_date = period_min
        else:
            # If period and date are given, the maximum of the min dates is choosed
            if period_min < date_min:
                self.min_date = date_min
            else:
                self.min_date = period_min


    def get_children_accounts(self, account, form):
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')
        self.child_ids = account_obj.search(self.cr, self.uid, [('parent_id', 'child_of', form['account_list'])])
        res = []
        ctx = self.ctx.copy()
        if account and account.child_consol_ids: # add ids of consolidated childs also of selected account
            ctx['consolidate_childs'] = True
            ctx['account_id'] = account.id
        ids_acc = account_obj.search(self.cr, self.uid,[('parent_id', 'child_of', [account.id])], context=ctx)
        for child_id in ids_acc:
            child_account = account_obj.browse(self.cr, self.uid, child_id)
            balance_account = self._sum_balance_account(child_account,form)
            self.balance_accounts[child_account.id] = balance_account
            if form['display_account'] == 'bal_mouvement':
                if child_account.type != 'view' \
                and len(move_line_obj.search(self.cr, self.uid,
                    [('account_id','=',child_account.id)],
                    context=ctx)) <> 0 :
                    res.append(child_account)
            elif form['display_account'] == 'bal_solde':
                if child_account.type != 'view' \
                and len(move_line_obj.search(self.cr, self.uid,
                    [('account_id','=',child_account.id)],
                    context=ctx)) <> 0 :
                    if balance_account <> 0.0:
                        res.append(child_account)
            else:
                if child_account.type != 'view' \
                and len(move_line_obj.search(self.cr, self.uid,
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
                    "WHERE l.account_id = " + str(move.id) +  " AND %s" % (self.query)
                self.cr.execute(sql_balance_init)
                resultat = self.cr.dictfetchall()
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


    def lines(self, account, form):
        inv_types = {
                'out_invoice': _('CI: '),
                'in_invoice': _('SI: '),
                'out_refund': _('OR: '),
                'in_refund': _('SR: '),
                }

        self.query

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
                               ORDER by %s""" % (self.query, sorttag)
        self.cr.execute(sql % account.id)

        res = self.cr.dictfetchall()
        move_line_obj = self.pool.get('account.move.line')
        account_obj = self.pool.get('account.account')
        invoice_obj = self.pool.get('account.invoice')

        # Balance from init fiscal year to last date given by the user
        accounts = account_obj.read(self.cr, self.uid, [account.id], ['balance'], self.ctxfy)
        sum = accounts[0]['balance']

        for l in reversed(res):
            line = move_line_obj.browse(self.cr, self.uid, l['id'])
            l['move'] = line.move_id.name_split
            self.cr.execute('Select id from account_invoice where move_id =%s'%(line.move_id.id))
            tmpres = self.cr.dictfetchall()
            if len(tmpres) > 0 :
                inv = invoice_obj.browse(self.cr, self.uid, tmpres[0]['id'])
                l['ref'] = inv_types[inv.type] + ': '+str(inv.number)
            if line.partner_id :
                l['partner'] = line.partner_id.name
            else :
                l['partner'] = ''
            l['line_corresp'] = self._calc_contrepartie(self.cr,self.uid,[l['id']])[l['id']]

            # Cumulative balance update
            l['progress'] = sum
            sum = sum - l['debit'] + l ['credit']

            # Modification of currency amount
            if (l['credit'] > 0):
                if l['amount_currency'] != None:
                    l['amount_currency'] = abs(l['amount_currency']) * -1
            if l['amount_currency'] != None:
                self.tot_currency = self.tot_currency + l['amount_currency']

        decimal_precision_obj = self.pool.get('decimal.precision')
        ids = decimal_precision_obj.search(self.cr, self.uid, [('name', '=', 'Account')])
        digits = decimal_precision_obj.browse(self.cr, self.uid, ids)[0].digits

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


    def _sum_debit_account(self, account, form):
        self.cr.execute("SELECT sum(debit) "\
                "FROM account_move_line l "\
                "WHERE l.account_id = %s AND %s " % (account.id, self.query))
        sum_debit = self.cr.fetchone()[0] or 0.0
        return sum_debit


    def _sum_credit_account(self, account, form):
        self.cr.execute("SELECT sum(credit) "\
                "FROM account_move_line l "\
                "WHERE l.account_id = %s AND %s " % (account.id, self.query))
        sum_credit = self.cr.fetchone()[0] or 0.0
        return sum_credit


    def _sum_balance_account(self, account, form):
        # Balance from init fiscal year to last date given by the user
        accounts = self.pool.get('account.account').read(self.cr, self.uid, [account.id], ['balance'], self.ctxfy)
        sum_balance = accounts[0]['balance']
        return sum_balance


    def _set_get_account_currency_code(self, account_id):
        self.cr.execute("SELECT c.symbol as code "\
                "FROM res_currency c, account_account as ac "\
                "WHERE ac.id = %s AND ac.currency_id = c.id" % (account_id))
        result = self.cr.fetchone()
        if result:
            self.account_currency = result[0]
        else:
            self.account_currency = False


    def _sum_currency_amount_account(self, account, form):
        self._set_get_account_currency_code(account.id)
        self.cr.execute("SELECT sum(l.amount_currency) "\
                "FROM account_move_line as l, res_currency as rc "\
                "WHERE l.currency_id = rc.id AND l.account_id= %s AND %s" % (account.id, self.query))
        total = self.cr.fetchone()
        if self.account_currency:
            return_field = str(total[0]) + self.account_currency
            return return_field
        else:
            currency_total = self.tot_currency = 0.0
            return currency_total


report_sxw.report_sxw('report.account.general.ledger.cumulative2', 'account.account', 'addons/account_financial_report/report/general_ledger.rml', parser=general_ledger, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
