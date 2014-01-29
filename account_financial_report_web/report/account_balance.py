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

import xml
import copy
from operator import itemgetter
import time
import datetime
from report import report_sxw
from tools import config
#import decimal_precision as dp

#import sys

class account_balance(report_sxw.rml_parse):
    _name = "report.account.balance.full2"
    

    def __init__(self, cr, uid, name, context):
        super(account_balance, self).__init__(cr, uid, name, context)
        self.sum_debit = 0.00
        self.sum_credit = 0.00
        self.sum_balance = 0.00
        self.sum_debit_fy = 0.00
        self.sum_credit_fy = 0.00
        self.sum_balance_fy = 0.00
        self.date_lst = []
        self.date_lst_string = ''
        self.localcontext.update({
            'time': time,
            'lines': self.lines,
            'get_fiscalyear_text': self.get_fiscalyear_text,
            'get_periods_and_date_text': self.get_periods_and_date_text,
        })
        self.context = context



    def set_context(self, objects, data, ids, report_type=None):
        new_ids = ids

        if (data['model'] == 'ir.ui.menu'):
            new_ids = data['form']['account_list']
            objects = self.pool.get('account.account').browse(self.cr, self.uid, new_ids)
        super(account_balance, self).set_context(objects, data, new_ids, report_type=report_type)

    def get_fiscalyear_text(self, form):
        """
        Returns the fiscal year text used on the report.
        """
        fiscalyear_obj = self.pool.get('account.fiscalyear')
        fiscalyear = None

        if form.get('fiscalyear'):

            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, form['fiscalyear'][0])

            return fiscalyear.name or fiscalyear.code
        else:
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear_obj.find(self.cr, self.uid))
            return "%s*" % (fiscalyear.name or fiscalyear.code)


    def get_periods_and_date_text(self, form):
        """
        Returns the text with the periods/dates used on the report.
        """
        period_obj = self.pool.get('account.period')
        periods_str = None
        fiscalyear_id = form['fiscalyear'] or fiscalyear_obj.find(self.cr, self.uid)
        period_ids = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear_id[0]),('special','=',False)])
        if form['state'] in ['byperiod', 'all']:
            period_ids = form['periods']
        periods_str = ', '.join([period.name or period.code for period in period_obj.browse(self.cr, self.uid, period_ids)])

        dates_str = None
        if form['state'] in ['bydate', 'all']:
            dates_str = self.formatLang(form['date_from'], date=True) + ' - ' + self.formatLang(form['date_to'], date=True) + ' '

        if periods_str and dates_str:
            return "%s / %s" % (periods_str, dates_str)
        elif periods_str:
            return "%s" % periods_str
        elif dates_str:
            return "%s" % dates_str
        else:
            return ''


    def lines(self, form, ids={}, done=None, level=0):
        """
        Returns all the data needed for the report lines
        (account info plus debit/credit/balance in the selected period
        and the full year)
        """

        if not ids:
            ids = self.ids
        if not ids:
            return []
        if not done:
            done = {}
        if form.has_key('account_list') and form['account_list']:
            account_ids = form['account_list']
            del form['account_list']
        res = {}
        result_acc = []
        accounts_levels = {}
        account_obj = self.pool.get('account.account')
        period_obj = self.pool.get('account.period')
        fiscalyear_obj = self.pool.get('account.fiscalyear')

        # Get the fiscal year
        fiscalyear = None
        if form.get('fiscalyear'):
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, form['fiscalyear'][0])
        else:
            fiscalyear = fiscalyear_obj.browse(self.cr, self.uid, fiscalyear_obj.find(self.cr, self.uid))

        #
        # Get the accounts
        #
        child_ids = account_obj._get_children_and_consol(self.cr, self.uid, account_ids, self.context)
        if child_ids:
            account_ids = child_ids

        #
        # Calculate the FY Balance.
        # (from full fiscal year without closing periods)
        #
        ctx = self.context.copy()

        if form.get('fiscalyear'):
            # Use only the current fiscal year
            ctx['fiscalyear'] = fiscalyear.id
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),'|',('special','=',False),('date_stop','<',fiscalyear.date_stop)])
        else:
            # Use all the open fiscal years
            open_fiscalyear_ids = fiscalyear_obj.search(self.cr, self.uid, [('state','=','draft')])
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','in',open_fiscalyear_ids),'|',('special','=',False),('date_stop','<',fiscalyear.date_stop)])

        fy_balance = {}
        for acc in account_obj.read(self.cr, self.uid, account_ids, ['balance'], ctx):
            fy_balance[acc['id']] = acc['balance']

        #
        # Calculate the FY Debit/Credit
        # (from full fiscal year without opening or closing periods)
        #
        ctx = self.context.copy()
        ctx['fiscalyear'] = fiscalyear.id
        ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)])

        fy_debit = {}
        fy_credit = {}
        for acc in account_obj.read(self.cr, self.uid, account_ids, ['debit','credit','balance'], ctx):
            fy_debit[acc['id']] = acc['debit']
            fy_credit[acc['id']] = acc['credit']

        #
        # Calculate the period Debit/Credit
        # (from the selected period or all the non special periods in the fy)
        #
        ctx = self.context.copy()
        """tx['state'] = form['context'].get('state','all')"""
        ctx['fiscalyear'] = fiscalyear.id
        ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)])
        if form['state'] in ['byperiod', 'all']:
            ctx['periods'] = form['periods']
        if form['state'] in ['bydate', 'all']:
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = form['date_to']

        accounts = account_obj.read(self.cr, self.uid, account_ids, ['type','code','name','debit','credit','balance','parent_id'], ctx)
        # In some versions of OpenERP server, the order of the read records differs from the order of the ids of the records
        accounts.sort(lambda x,y: cmp(x['code'], y['code']))

        #
        # Calculate the period initial Balance
        # (fy balance minus the balance from the start of the selected period
        #  to the end of the year)
        #
        ctx = self.context.copy()
        """ctx['state'] = form['context'].get('state','all')"""
        ctx['fiscalyear'] = fiscalyear.id
        ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('special','=',False)])
        if form['state'] in ['byperiod', 'all']:
            ctx['periods'] = form['periods']    
            date_start = min([period.date_start for period in period_obj.browse(self.cr, self.uid, ctx['periods'])])
            ctx['periods'] = period_obj.search(self.cr, self.uid, [('fiscalyear_id','=',fiscalyear.id),('date_start','>=',date_start),('special','=',False)])
        if form['state'] in ['bydate', 'all']:
            ctx['date_from'] = form['date_from']
            ctx['date_to'] = fiscalyear.date_stop

        period_balanceinit = {}
        for acc in account_obj.read(self.cr, self.uid, account_ids, ['balance'], ctx):
            period_balanceinit[acc['id']] = fy_balance[acc['id']] - acc['balance']

        #
        # Generate the report lines (checking each account)
        #
        decimal_precision_obj = self.pool.get('decimal.precision')
        ids = decimal_precision_obj.search(self.cr, self.uid, [('name', '=', 'Account')])
        digits = decimal_precision_obj.browse(self.cr, self.uid, ids)[0].digits
        #print >>sys.stderr, 'digits',digits

        for account in accounts:
            account_id = account['id']

            if account_id in done:
                continue

            done[account_id] = 1

            #
            # Calculate the account level
            #
            parent_id = account['parent_id']
            if parent_id:
                if isinstance(parent_id, tuple):
                    parent_id = parent_id[0]
                account_level = accounts_levels.get(parent_id, 0) + 1
            else:
                account_level = level
            accounts_levels[account_id] = account_level

            #
            # Check if we need to include this level
            #
            if not form['display_account_level'] or account_level <= form['display_account_level']:
                #
                # Copy the account values
                #
                res = {
                        'id' : account_id,
                        'type' : account['type'],
                        'code': account['code'],
                        'name': account['name'],
                        'level': account_level,
                        'balanceinit': period_balanceinit[account_id],
                        'debit': account['debit'],
                        'credit': account['credit'],
                        'balance': period_balanceinit[account_id]+account['balance'],
                        'balanceinit_fy': fy_balance[account_id]-fy_debit[account_id]+fy_credit[account_id],
                        'debit_fy': fy_debit[account_id],
                        'credit_fy': fy_credit[account_id],
                        'balance_fy': fy_balance[account_id],
                        'parent_id': account['parent_id'],
                        'bal_type': '',
                    }

                #
                # Round the values to zero if needed (-0.000001 ~= 0)
                #
                res['balance'] = round(res['balance'],digits)
                res['balance_fy'] = round(res['balance_fy'],digits)
                res['balanceinit'] = round(res['balanceinit'],digits)
                res['balanceinit_fy'] = round(res['balanceinit_fy'],digits)
                res['debit'] = round(res['debit'],digits)
                res['credit'] = round(res['credit'],digits)
                #if abs(res['balance']) < 0.5 * 10**-int(config['price_accuracy']):
                #    res['balance'] = 0.0
                #if abs(res['balance_fy']) < 0.5 * 10**-int(config['price_accuracy']):
                #    res['balance_fy'] = 0.0
                #if abs(res['balanceinit']) < 0.5 * 10**-int(config['price_accuracy']):
                #    res['balanceinit'] = 0.0
                #if abs(res['balanceinit_fy']) < 0.5 * 10**-int(config['price_accuracy']):
                #    res['balanceinit_fy'] = 0.0

                #
                # Check whether we must include this line in the report or not
                #
                if form['display_account'] == 'bal_mouvement' and account['parent_id']:
                    # Include accounts with movements
                    if res['balance'] <> 0.0 \
                            or res['debit'] <> 0.0 \
                            or res['credit'] <> 0.0:
                #    if abs(res['balance']) >= 0.5 * 10**-int(config['price_accuracy']) \
                #            or abs(res['credit']) >= 0.5 * 10**-int(config['price_accuracy']) \
                #            or abs(res['debit']) >= 0.5 * 10**-int(config['price_accuracy']):
                        result_acc.append(res)
                elif form['display_account'] == 'bal_solde' and account['parent_id']:
                    # Include accounts with balance
                    #if abs(res['balance']) >= 0.5 * 10**-int(config['price_accuracy']):
                    if res['balance'] <> 0.0 :
                        result_acc.append(res)
                else:
                    # Include all accounts
                    result_acc.append(res)
        return result_acc

report_sxw.report_sxw('report.account.balance.full2', 'account.account', 'addons/account_financial_report/report/account_balance_full.rml', parser=account_balance, header=False)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
