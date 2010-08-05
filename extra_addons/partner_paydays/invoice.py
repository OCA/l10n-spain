##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2010 NaN Projectes de Programari Lliure, S.L.  All Rights Reserved
#                       http://www.NaN-tic.com
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

from osv import osv
from osv import fields
import datetime
import time
from tools.translate import _

class account_invoice(osv.osv):
    _inherit = 'account.invoice'

    def onchange_payment_term_date_invoice(self, cr, uid, ids, payment_term_id, date_invoice, partner_id, context=None):
        if context is None:
            context = {}

        if not payment_term_id:
            return {}
        res={}
        pt_obj= self.pool.get('account.payment.term')
        if not date_invoice :
            date_invoice = time.strftime('%Y-%m-%d')

        context['partner_id'] = partner_id

        pterm_list = pt_obj.compute(cr, uid, payment_term_id, value=1, date_ref=date_invoice, context=context)

        if pterm_list:
            pterm_list = [line[0] for line in pterm_list]
            pterm_list.sort()
            res= {'value':{'date_due': pterm_list[-1]}}
        else:
             raise osv.except_osv(_('Data Insufficient !'), _('The Payment Term of Partner does not have Payment Term Lines(Computation) defined !'))

        return res

    def action_date_assign(self, cr, uid, ids, *args):
        for inv in self.browse(cr, uid, ids):
            res = self.onchange_payment_term_date_invoice(cr, uid, inv.id, inv.payment_term.id, inv.date_invoice, inv.partner_id.id)
            if res and res['value']:
                self.write(cr, uid, [inv.id], res['value'])
        return True

    def action_move_create(self, cr, uid, ids, *args):
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        context = {}
        for inv in self.browse(cr, uid, ids):
            if inv.move_id:
                continue

            if not inv.date_invoice:
                self.write(cr, uid, [inv.id], {'date_invoice':time.strftime('%Y-%m-%d')})
            company_currency = inv.company_id.currency_id.id
            # create the analytical lines
            line_ids = self.read(cr, uid, [inv.id], ['invoice_line'])[0]['invoice_line']
            # one move line per invoice line
            iml = self._get_analytic_lines(cr, uid, inv.id)
            # check if taxes are all computed

            context.update({'lang': inv.partner_id.lang})
            compute_taxes = ait_obj.compute(cr, uid, inv.id, context=context)
            if not inv.tax_line:
                for tax in compute_taxes.values():
                    ait_obj.create(cr, uid, tax)
            else:
                tax_key = []
                for tax in inv.tax_line:
                    if tax.manual:
                        continue
                    key = (tax.tax_code_id.id, tax.base_code_id.id, tax.account_id.id)
                    tax_key.append(key)
                    if not key in compute_taxes:
                        raise osv.except_osv(_('Warning !'), _('Global taxes defined, but are not in invoice lines !'))
                    base = compute_taxes[key]['base']
                    if abs(base - tax.base) > inv.company_id.currency_id.rounding:
                        raise osv.except_osv(_('Warning !'), _('Tax base different !\nClick on compute to update tax base'))
                for key in compute_taxes:
                    if not key in tax_key:
                        raise osv.except_osv(_('Warning !'), _('Taxes missing !'))

            if inv.type in ('in_invoice', 'in_refund') and abs(inv.check_total - inv.amount_total) >= (inv.currency_id.rounding/2.0):
                raise osv.except_osv(_('Bad total !'), _('Please verify the price of the invoice !\nThe real total does not match the computed total.'))

            # one move line per tax line
            iml += ait_obj.move_line_get(cr, uid, inv.id)

            if inv.type in ('in_invoice', 'in_refund'):
                ref = inv.reference
            else:
                ref = self._convert_ref(cr, uid, inv.number)

            diff_currency_p = inv.currency_id.id <> company_currency
            # create one move line for the total and possibly adjust the other lines amount
            total = 0
            total_currency = 0
            for i in iml:
                if inv.currency_id.id != company_currency:
                    i['currency_id'] = inv.currency_id.id
                    i['amount_currency'] = i['price']
                    i['price'] = cur_obj.compute(cr, uid, inv.currency_id.id,
                            company_currency, i['price'],
                            context={'date': inv.date_invoice or time.strftime('%Y-%m-%d')})
                else:
                    i['amount_currency'] = False
                    i['currency_id'] = False
                i['ref'] = ref
                if inv.type in ('out_invoice','in_refund'):
                    total += i['price']
                    total_currency += i['amount_currency'] or i['price']
                    i['price'] = - i['price']
                else:
                    total -= i['price']
                    total_currency -= i['amount_currency'] or i['price']
            acc_id = inv.account_id.id

            name = inv['name'] or '/'
            totlines = False
            if inv.payment_term:
                context = {
                    'partner_id': inv.partner_id.id
                }
                totlines = self.pool.get('account.payment.term').compute(cr,
                        uid, inv.payment_term.id, total, inv.date_invoice or False, context)
            if totlines:
                res_amount_currency = total_currency
                i = 0
                for t in totlines:
                    if inv.currency_id.id != company_currency:
                        amount_currency = cur_obj.compute(cr, uid,
                                company_currency, inv.currency_id.id, t[1])
                    else:
                        amount_currency = False

                    # last line add the diff
                    res_amount_currency -= amount_currency or 0
                    i += 1
                    if i == len(totlines):
                        amount_currency += res_amount_currency

                    iml.append({
                        'type': 'dest',
                        'name': name,
                        'price': t[1],
                        'account_id': acc_id,
                        'date_maturity': t[0],
                        'amount_currency': diff_currency_p \
                                and  amount_currency or False,
                        'currency_id': diff_currency_p \
                                and inv.currency_id.id or False,
                        'ref': ref,
                    })
            else:
                iml.append({
                    'type': 'dest',
                    'name': name,
                    'price': total,
                    'account_id': acc_id,
                    'date_maturity' : inv.date_due or False,
                    'amount_currency': diff_currency_p \
                            and total_currency or False,
                    'currency_id': diff_currency_p \
                            and inv.currency_id.id or False,
                    'ref': ref
            })

            date = inv.date_invoice or time.strftime('%Y-%m-%d')
            part = inv.partner_id.id

            line = map(lambda x:(0,0,self.line_get_convert(cr, uid, x, part, date, context={})) ,iml)

            if inv.journal_id.group_invoice_lines:
                line2 = {}
                for x, y, l in line:
                    tmp = str(l['account_id'])
                    tmp += '-'+str(l.get('tax_code_id',"False"))
                    tmp += '-'+str(l.get('product_id',"False"))
                    tmp += '-'+str(l.get('analytic_account_id',"False"))
                    tmp += '-'+str(l.get('date_maturity',"False"))

                    if tmp in line2:
                        am = line2[tmp]['debit'] - line2[tmp]['credit'] + (l['debit'] - l['credit'])
                        line2[tmp]['debit'] = (am > 0) and am or 0.0
                        line2[tmp]['credit'] = (am < 0) and -am or 0.0
                        line2[tmp]['tax_amount'] += l['tax_amount']
                        line2[tmp]['analytic_lines'] += l['analytic_lines']
                    else:
                        line2[tmp] = l
                line = []
                for key, val in line2.items():
                    line.append((0,0,val))

            journal_id = inv.journal_id.id #self._get_journal(cr, uid, {'type': inv['type']})
            journal = self.pool.get('account.journal').browse(cr, uid, journal_id)
            if journal.centralisation:
                raise osv.except_osv(_('UserError'),
                        _('Cannot create invoice move on centralised journal'))

            line = self.finalize_invoice_move_lines(cr, uid, inv, line)

            move = {'ref': inv.number, 'line_id': line, 'journal_id': journal_id, 'date': date}
            period_id=inv.period_id and inv.period_id.id or False
            if not period_id:
                period_ids= self.pool.get('account.period').search(cr,uid,[('date_start','<=',inv.date_invoice or time.strftime('%Y-%m-%d')),('date_stop','>=',inv.date_invoice or time.strftime('%Y-%m-%d'))])
                if len(period_ids):
                    period_id=period_ids[0]
            if period_id:
                move['period_id'] = period_id
                for i in line:
                    i[2]['period_id'] = period_id

            move_id = self.pool.get('account.move').create(cr, uid, move, context=context)
            new_move_name = self.pool.get('account.move').browse(cr, uid, move_id).name
            # make the invoice point to that move
            self.write(cr, uid, [inv.id], {'move_id': move_id,'period_id':period_id, 'move_name':new_move_name})
            self.pool.get('account.move').post(cr, uid, [move_id])
        self._log_event(cr, uid, ids)
        return True

account_invoice()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
