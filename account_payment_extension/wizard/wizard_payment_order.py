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
import time


class wizard_line_list(osv.osv_memory):
    _name = 'wizard.line.list'
    
    _columns={
              'entries':fields.many2many('account.move.line','rel_move_lines','payment_id','line_id','Entries'),
              'communication2':fields.char ('Communication 2',size = 64, help ='The successor message of payment communication.'),
              }

    def create_payment(self, cr, uid, ids, context):
        ###########################################################
        # OBJETOS
        ###########################################################
        order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('account.move.line')
        payment_line_obj = self.pool.get('payment.line')
        currency_obj = self.pool.get('res.currency')
        ###########################################################
        line_ids =[]
        if not isinstance(ids,list):
            ids=[ids]
        line_ids_o= self.browse(cr,uid,ids[0]).entries
        for line_o in line_ids_o:
            line_ids.append(line_o.id)
        if not line_ids: return {}
    
        pool= pooler.get_pool(cr.dbname)
        order_id = context['payment_order']
        payment = order_obj.browse(cr, uid, order_id,context=context)
        t = payment.mode and payment.mode.type.id or None
        line2bank = line_obj.line2bank(cr, uid, line_ids, t, context)
    
        ## Finally populate the current payment with new lines:
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if payment.date_prefered == "now":
                #no payment date => immediate payment
                date_to_pay = False
            elif payment.date_prefered == 'due':
                date_to_pay = line.date_maturity
            elif payment.date_prefered == 'fixed':
                date_to_pay = payment.date_scheduled
    
            if payment.type == 'payable':
                amount_to_pay = line.amount_to_pay
            else:
                amount_to_pay = -line.amount_to_pay
            val ={
                  'move_line_id': line.id,
                  'amount_currency': amount_to_pay,
                  'bank_id': line2bank.get(line.id),
                  'order_id': payment.id,
                  'partner_id': line.partner_id and line.partner_id.id or False,
                  'communication': (line.ref and line.name!='/' and line.ref+'. '+line.name) or line.ref or line.name or '/',
                  'communication2': self.browse(cr,uid,ids[0]).communication2,
                  'date': date_to_pay,
                  'currency':currency_obj.search(cr,uid,[])[0],
                  'account_id': line.account_id.id,
                  'type':payment.type,
                  
                  }
            if line.invoice:
                if line.invoice.currency_id:
                    val.update({ 'currency':line.invoice.currency_id.id})
            payment_line_obj.create(cr,uid,val, context=context)
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'}
    
wizard_line_list()
class wizard_payment_order(osv.osv_memory):
    """
    Create a payment object with lines corresponding to the account move line
    to pay according to the date provided by the user and the mode-type payment of the order.
    Hypothesis:
    - Small number of non-reconcilied move line , payment mode and bank account type,
    - Big number of partner and bank account.

    If a type is given, unsuitable account move lines are ignored.
    """
    _name = 'wizard.payment.order'
    _description = 'Para crear nominas'
    
    _columns={
              'duedate': fields.date ('Due Date',required = True),
              'amount':fields.float ('Amount', help ='Next step will automatically select payments up to this amount as long as account moves have bank account if that is required by the selected payment mode.'),
              'show_refunds':fields.boolean('Show Refunds', help = 'Indicates if search should include refunds.'),
              }
    
    _defaults={
               'duedate':lambda *a: time.strftime('%Y-%m-%d'),
               'show_refunds': lambda *a: False
               
               }
    
    
#############################################################################################
    
    def search_entries(self, cr, uid, ids, context):
        
        ######################################################
        # OBJETOS
        ######################################################
        pool = pooler.get_pool(cr.dbname)
        order_obj = self.pool.get('payment.order')
        line_obj = self.pool.get('account.move.line')
        ######################################################
        
        #search_due_date = data['form']['duedate']
        #show_refunds = data['form']['show_refunds']
        
        search_due_date = self.browse(cr, uid, ids[0], context).duedate
        show_refunds = self.browse(cr, uid, ids[0], context).show_refunds
    
        payment = order_obj.browse(cr, uid, context.get('active_id'), context=context)
        ctx = ''
        if payment.mode:
            ctx = '''context="{'journal_id': %d}"''' % payment.mode.journal.id
    
        # Search for move line to pay:
        domain = [('reconcile_id', '=', False),('account_id.type', '=', payment.type),('amount_to_pay', '<>', 0)]
    
        if payment.type =='payable' and not show_refunds:
            domain += [ ('credit','>',0) ]
            
        elif not show_refunds:
            domain += [ ('debit','>',0) ]
    
        if payment.mode:
            domain += [ ('payment_type','=',payment.mode.type.id) ]
    
        domain += ['|',('date_maturity','<',search_due_date),('date_maturity','=',False)]
        line_ids = line_obj.search(cr, uid, domain, order='date_maturity', context=context)
    
    
    #    FORM.string = '''<?xml version="1.0" encoding="utf-8"?>
    #<form string="Populate Payment:">
    #    <field name="entries" colspan="4" height="300" width="800" nolabel="1" domain="[('id', 'in', [%s])]" %s/>
    #    <separator string="Extra message of payment communication" colspan="4"/>
    #    <field name="communication2" colspan="4"/>
    #</form>''' % (','.join([str(x) for x in line_ids]), ctx)
    
        selected_ids = []
    
    
    #    if payment.mode.require_bank_account and not line.partner_bank_id:
    #        continue
    #    if payment.mode.require_same_bank_account:
    #        if not line.partner_bank_id:
    #            continue
    #        mode_account = payment.mode.bank_id.acc_number or payment.mode.bank_id.iban
    #        line_account = line.partner_bank_id.acc_number or line.partner_bank_id.iban
    #        if mode_account != line_account:
    #            continue
    #    if payment.mode.require_received_check:
    #        if not line.received_check:
    #            continue
    
        #amount = data['form']['amount']
        amount = self.browse(cr, uid, ids[0], context).amount
        if amount:
            if payment.mode and payment.mode.require_bank_account:
                line2bank = line_obj.line2bank(cr, uid, line_ids, payment.mode.id, context)
            else:
                line2bank = None
            # If user specified an amount, search what moves match the criteria taking into account
            # if payment mode allows bank account to be null.
            for line in line_obj.browse(cr, uid, line_ids, context):
                if abs(line.amount_to_pay) <= amount:
                    amount -= abs(line.amount_to_pay)
                    selected_ids.append( line.id )
        
        
        wiz_id = self.pool.get('wizard.line.list').create(cr,uid,{'entries':[(6,0,selected_ids)]})   
        context.update({'payment_order':payment.id})
        mod_obj = self.pool.get('ir.model.data')
        form_res1 = mod_obj.get_object_reference(cr, uid, 'account_payment_extension', 'wizard_line_list_py_form_view')
        form_id1 = form_res1 and form_res1[1] or False
        form_res2 = mod_obj.get_object_reference(cr, uid, 'account_payment_extension', 'wizard_line_list_re_form_view')
        form_id2 = form_res2 and form_res2[1] or False
        if payment.type == 'payable':
            wizard = {
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.line.list',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(form_id1, 'form')],
                'res_id':wiz_id,
                'target': 'new',
                'context': context
                }
        else:
             wizard = {
                'type': 'ir.actions.act_window',
                'res_model': 'wizard.line.list',
                'view_type': 'form',
                'view_mode': 'form',
                'views': [(form_id2, 'form')],
                'res_id':wiz_id,
                'target': 'new',
                'context': context
                }
        return wizard
    
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'}

wizard_payment_order()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
