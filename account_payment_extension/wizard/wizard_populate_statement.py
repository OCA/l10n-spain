# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution	
#    Copyright (C) 2004-2008 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    AvanzOSC, Avanzed Open Source Consulting 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
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

from osv import osv, fields
import wizard
import pooler
from tools.misc import UpdateableStr

#FORM = UpdateableStr()
#FIELDS = {
#    'lines': {'string': 'Payment Lines', 'type': 'many2many',
#        'relation': 'payment.line'},
#}

class wizard_populate_statement(osv.osv_memory):
    """
    Populate the current statement with selected payement lines
    """
    _name = 'wizard.populate.statement'
    _description = ''
    
    _columns = {
               #'lines': {'string': 'Payment Lines', 'type': 'many2many','relation': 'payment.line'},
               'lines': fields.many2many('payment.line', 'rel_populate_statement', 'line_id', 'payment_id', 'Payment Lines'),
              }
    
    _defaults = {
                 'lines': lambda self,cr,uid,c: self.search_entries(cr,uid,c)
                 }
    def search_entries(self, cr, uid, context):
        ########################################################
        # OBJETOS
        ########################################################
        pool = pooler.get_pool(cr.dbname)
        line_obj = self.pool.get('payment.line')
        statement_obj = self.pool.get('account.bank.statement')
        ########################################################
        res = {}
        ids = context['active_id']
        if context['active_model'] == 'account.bank.statement':
            statement = statement_obj.browse(cr, uid, ids, context=context)
            line_ids = line_obj.search(cr, uid, [
                ('move_line_id.reconcile_id', '=', False),
                ('order_id.mode.journal.id', '=', statement.journal_id.id)])
        
            line_ids.extend(line_obj.search(cr, uid, [
                ('move_line_id.reconcile_id', '=', False),
                ('order_id.mode', '=', False)]))
            res=line_ids
#    FORM.string = '''<?xml version="1.0"?>
#<form string="Populate Statement:">
#    <field name="lines" colspan="4" height="300" width="800" nolabel="1"
#        domain="[('id', 'in', [%s])]"/>
#</form>''' % (','.join([str(x) for x in line_ids]))
        return res

    def populate_statement(self, cr, uid, ids, context):
        ######################################################
        # OBJETOS
        ######################################################
        #pool = pooler.get_pool(cr.dbname)
        line_obj = self.pool.get('payment.line')
        statement_obj = self.pool.get('account.bank.statement')
        statement_line_obj = self.pool.get('account.bank.statement.line')
        currency_obj = self.pool.get('res.currency')
        move_line_obj = self.pool.get('account.move.line')
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        ######################################################
        #line_ids = data['form']['lines'][0][2]
        if not isinstance(ids,list):
            ids = [ids]
        line_ids = self.browse(cr, uid, ids[0], context).lines
        if not line_ids:
            return {}
        statement = statement_obj.browse(cr, uid, context['active_id'], context=context)
    
        for line in line_ids:
            ctx = context.copy()
            ctx['date'] = line.ml_maturity_date
            amount_currency = line.type == 'payment' and line.amount_currency or -line.amount_currency
            amount = currency_obj.compute(cr, uid, line.currency.id, statement.currency.id, amount_currency, context=ctx)
    
            voucher_id = False
            if line.move_line_id:
                #We have to create a voucher and link it to the bank statement line
                context.update({'move_line_ids': [line.move_line_id.id]})
                result = voucher_obj.onchange_partner_id(cr, uid, [], partner_id=line.move_line_id.partner_id.id,
                    journal_id=statement.journal_id.id, price=abs(amount), currency_id=statement.currency.id,
                    ttype=(amount < 0 and 'payment' or 'receipt'), date=line.date or line.move_line_id.date, context=context)
    
                voucher_res = { 
                            'type':(amount < 0 and 'payment' or 'receipt'),
                            'name': line.move_line_id.name,
                            'reference': (line.order_id.reference or '?') + '. ' + line.name,
                            'partner_id': line.move_line_id.partner_id.id,
                            'journal_id': statement.journal_id.id,
                            'account_id': result.get('account_id', statement.journal_id.default_credit_account_id.id), # improve me: statement.journal_id.default_credit_account_id.id
                            'company_id': statement.company_id.id,
                            'currency_id': statement.currency.id,
                            'date': line.date or line.move_line_id.date,
                            'amount': abs(amount),
                            'period_id': statement.period_id.id
                                }
                voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)
    
                voucher_line_dict = {}
                if result['value']['line_ids']:
                    for line_dict in result['value']['line_ids']:
                        move_line = move_line_obj.browse(cr, uid, line_dict['move_line_id'], context)
                        if line.move_line_id.move_id.id == move_line.move_id.id:
                            voucher_line_dict = line_dict
                if voucher_line_dict:
                    voucher_line_dict.update({'voucher_id': voucher_id, 'amount': abs(amount)})
                    voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)
            val = {
                'name': (line.order_id.reference or '?') + '. ' + line.name,
                #Tipically: type=='payable' => amount>0  type=='receivable' => amount<0
                'amount': line.type == 'payable' and amount or -amount,
                'type': line.order_id.type == 'payable' and 'supplier' or 'customer',
                'partner_id': line.partner_id.id,
                'account_id': line.move_line_id.account_id.id,
                'statement_id': statement.id,
                'ref': line.communication,
                'voucher_id': voucher_id,
                   }        
    
            statement_line_obj.create(cr, uid, val, context=context)
        return {}

    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'}

wizard_populate_statement()




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

