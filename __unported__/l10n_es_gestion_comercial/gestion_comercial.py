# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) 2011 Soluntec - Soluciones Tecnológicas (http://www.soluntec.es) All Rights Reserved.
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
##############################################################################


from osv import fields, osv
from openerp import netsvc
from openerp.tools import config
import account_check

#
# Diarios
#
#==================================================================================
#============================== INHERIT CLASS ACCOUNT JOURNAL======================
#==================================================================================
#Se modifica la clase de diarios contables para añadir nuevos campos que serán luego utilizados
#para determinar el comportamiento de los comprobantes de paggo

class account_journal(osv.osv):

# Se añaden a los comprobantes de pago, los campos de cheque recibido y de pago indirecto. 
# el campo de pago indirecto es un campo no visible, que se utilizará para registrar aquellos pagos que corresponden
# a documentos bancarios, es decir que no abonan directamente la factura sino que agrupan la deuda en un nuevo efecto cobrable

    _inherit = 'account.journal'
    _name = 'account.journal'
    _columns = {
         'indirect_payment': fields.boolean('Gestión de efectos comerciales', help="Marcar si se va a utilizar este diario para registrar apuntes de efectos correspondiente a gestión comercial (pagarés, giros, cheques, etc). El sistema usuará la cuenta definida en la ficha de cliente. Si está en blanco usuará la definida en este diario"),
         'without_account_efect': fields.boolean('Sin efecto contable', help="Si se marca esta opción, el sistema usará la cuenta de cobrables/pagables del cliente en lugar de la cuenta de fectos definidas en el diario o cliente"),
         'indirect_payment_type': fields.selection([('documento','Documento de Cobro'),('impago','Impagos'),('incobrable','Incobrable')],'Tipo de Efecto Comercial', select=True),
		 'gestion_cobro': fields.boolean('Gestión de cobro', help="Marque esta opción si el diario será utilizado para operaciones de gestión de cobro"),
         'descuento_efectos': fields.boolean('Descuento de Efectos', help="Marque esta opción si el diario será utilizado para operaciones de- descuento de efectos"),
		 'property_account_descuento_efectos': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Cuenta de descuento de Efectos",
            method=True,
            view_load=True,
            required=False),
    
    }

account_journal()


#
# Partners
#
#==================================================================================
#============================== INHERIT CLASS RES_PARTNER==========================
#==================================================================================
#Se añade campos a los partners para registrar las cuentas a utilizar para efectos comerciales

class res_partner(osv.osv):

    _inherit = 'res.partner'
    _name = 'res.partner'
    
    
    _columns = {
        'property_account_efectos_cartera': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Efectos Comerciales en Cartera",
            method=True,
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="Esta cuenta será utilizada en lugar de la cuenta por defecto del diario para registrar los efectos comerciales en cartera",
            required=False),
        'property_account_impagos': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Impagos",
            method=True,
            view_load=True,
            domain="[('type', '=', 'receivable')]",
            help="Esta cuenta será utilizada en lugar de la cuenta por defecto del diario para registrar los efectos impagados",
            required=False),
        'property_account_efectos_incobrables': fields.property(
            'account.account',
            type='many2one',
            relation='account.account',
            string="Incobrables",
            method=True,
            view_load=True,
            domain="[('type', '=', 'other')]",
            help="Esta cuenta será utilizada en lugar de la cuenta por defecto para registrar los efectos incobrables",
            required=False),
    }

res_partner()




#
# Comprobantes de Pago
#
#==================================================================================
#============================== INHERIT CLASS ACCOUNT VOUCHER======================
#==================================================================================
#Se modifica la gestión de comprobantes de pago para que amplie la funcionalidad para
#registrar pagos mediante pagarés,cheques, etc..

class account_voucher(osv.osv):

# Se añaden a los comprobantes de pago, los campos de cheque recibido y de pago indirecto. 
# el campo de pago indirecto es un campo no visible, que se utilizará para registrar aquellos pagos que corresponden
# a documentos bancarios, es decir que no abonan directamente la factura sino que agrupan la deuda en un nuevo efecto cobrable

    _inherit = 'account.voucher'
    _name = 'account.voucher'
    
    #================= METHODS =================#
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, amount, currency_id, ttype, date, context=None):
            
        # We call the original event to give us back the original values
        res = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, amount, currency_id, type, date)
        
        if journal_id:
            
            journal_pool = self.pool.get('account.journal')
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
                    
          
            if journal.indirect_payment:
                res['value']['indirect_payment'] = True
            else:
                res['value']['indirect_payment'] = False    
        
        return res
    
    def action_move_line_create(self, cr, uid, ids, context=None):

        def _get_payment_term_lines(term_id, amount):
            term_pool = self.pool.get('account.payment.term')
            if term_id and amount:
                terms = term_pool.compute(cr, uid, term_id, amount)
                return terms
            return False
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        tax_obj = self.pool.get('account.tax')
        seq_obj = self.pool.get('ir.sequence')
        for inv in self.browse(cr, uid, ids, context=context):
            if inv.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            if not inv.reference:
                ref = name.replace('/','')
            else:
                ref = inv.reference

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.narration,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            # TODO: is there any other alternative then the voucher type ??
            # -for sale, purchase we have but for the payment and receipt we do not have as based on the bank/cash journal we can not know its payment or receipt
            if inv.type in ('purchase', 'payment'):
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            elif inv.type in ('sale', 'receipt'):
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the voucher
            
            #Lineas modificadas respecto al original
            cuenta_id = False
            if inv.journal_id.indirect_payment:
                if inv.journal_id.without_account_efect:
                    cuenta_id = inv.partner_id.property_account_receivable.id,
                else:
                    if inv.journal_id.indirect_payment_type == "documento":
                        if inv.partner_id.property_account_efectos_cartera.id:
                            cuenta_id = inv.partner_id.property_account_efectos_cartera.id,
                        else:
                            cuenta_id = inv.account_id.id,
                    elif inv.journal_id.indirect_payment_type == "impago":
                        if inv.partner_id.property_account_impagos.id:
                            cuenta_id = inv.partner_id.property_account_impagos.id,
                        else:
                            cuenta_id = inv.account_id.id,
                    elif inv.journal_id.indirect_payment_type == "incobrable":
                        if inv.partner_id.property_account_efectos_incobrables.id:
                            cuenta_id = inv.partner_id.property_account_efectos_incobrables.id,
                        else:
                            cuenta_id = inv.account_id.id,                                
            else:
                cuenta_id = inv.account_id.id,
                          
            move_line = {
                'name': inv.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': cuenta_id[0],
                'move_id': move_id,
                'journal_id': inv.journal_id.id,
                'period_id': inv.period_id.id,
                'partner_id': inv.partner_id.id,
                'currency_id': company_currency <> current_currency and current_currency or company_currency,
                'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                'date': inv.date,
                'date_maturity': inv.date_due
            }
            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            if inv.type == 'sale':
                line_total = line_total - currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)
            elif inv.type == 'purchase':
                line_total = line_total + currency_pool.compute(cr, uid, inv.currency_id.id, company_currency, inv.tax_amount, context=context_multi_currency)

            for line in inv.line_ids:
                #create one move line per voucher line where amount is not 0.0
                if not line.amount:
                    continue
                #we check if the voucher line is fully paid or not and create a move line to balance the payment and initial invoice if needed
                if line.amount == line.amount_unreconciled:
                    amount = line.move_line_id.amount_residual #residual amount in company currency
                else:
                    amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.untax_amount or line.amount, context=context_multi_currency)
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or company_currency,
                    'analytic_account_id': line.account_analytic_id and line.account_analytic_id.id or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'

                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount

                if inv.tax_id and inv.type in ('sale', 'purchase'):
                    move_line.update({
                        'account_tax_id': inv.tax_id.id,
                    })
                if move_line.get('account_tax_id', False):
                    tax_data = tax_obj.browse(cr, uid, [move_line['account_tax_id']], context=context)[0]
                    if not (tax_data.base_code_id and tax_data.tax_code_id):
                        raise osv.except_osv(_('No Account Base Code and Account Tax Code!'),_("You have to configure account base code and account tax code on the '%s' tax!") % (tax_data.name))
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
                voucher_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [voucher_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)

            if not currency_pool.is_zero(cr, uid, inv.currency_id, line_total):
                diff = line_total
                account_id = False
                if inv.payment_option == 'with_writeoff':
                    account_id = inv.writeoff_acc_id.id
                elif inv.type in ('sale', 'receipt'):
                    account_id = inv.partner_id.property_account_receivable.id
                else:
                    account_id = inv.partner_id.property_account_payable.id
                move_line = {
                    'name': name,
                    'account_id': account_id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'date': inv.date,
                    'credit': diff > 0 and diff or 0.0,
                    'debit': diff < 0 and -diff or 0.0,
                    #'amount_currency': company_currency <> current_currency and currency_pool.compute(cr, uid, company_currency, current_currency, diff * -1, context=context_multi_currency) or 0.0,
                    #'currency_id': company_currency <> current_currency and current_currency or False,
                }
                move_line_pool.create(cr, uid, move_line)
            self.write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
            for rec_ids in rec_list_ids:
                if len(rec_ids) >= 2:
                    move_line_pool.reconcile_partial(cr, uid, rec_ids)
        return True
       
    #================= FIELDS =================#
    _columns = {
         'payment_type': fields.many2one('payment.type', 'Tipo de Pago', help="Tipo de pago establecido para el nuevo efecto a crear"),
         'received_check': fields.boolean('Received check', help="To write down that a check in paper support has been received, for example.", invisible=True),
         'indirect_payment': fields.boolean('Document check', help="To mark if is not a direct payment"),
         'issued_check_ids':fields.one2many('account.issued.check', 'voucher_id', 'Cheques emitidos'),
         'third_check_receipt_ids':fields.one2many('account.third.check', 'voucher_id', 'Cheques de Terceros', required=False),
         'third_check_ids':fields.many2many('account.third.check', 'third_check_voucher_rel', 'third_check_id', 'voucher_id', 'Cheques de Terceros'),
         'property_account_gastos': fields.property(
             'account.account',
             type='many2one',
             relation='account.account',
             string="Cuenta Gastos",
             method=True,
             view_load=True,
             domain="[('type', '=', 'other')]",
             help="Gastos ocasionados por el impago",
             required=False), 
         'expense_amount': fields.float('Cantidad Gastos'),
         'invoice_expense':fields.boolean('Facturar Gastos?'),        

    }
    

account_voucher()


#
# Apuntes contables
#
#==================================================================================
#============================== INHERIT CLASS ACCOUNT VOUCHER======================
#==================================================================================
#Se realizan los siguientes cambios....
#Se sobreescribe el campo funcional de tipo de pago con una nueva versión que hace lo mismo pero buscando ademas 
#el valor del comprante de pago si el efecto no esta relacionado directamente con una factura

class account_move_line(osv.osv):
    _name = 'account.move.line'
    _inherit = 'account.move.line'

# Se amplia el metodo original de account_payment_extension. Ahora si no encuentra el tipo de pago en la factura 
# asociada el apunte, lo busca en el comprobante de pago... Si no esta en ninguno de los dos, lo deja en blanco.  
    def _payment_type_get(self, cr, uid, ids, field_name, arg, context={}):
        result = {}
        invoice_obj = self.pool.get('account.invoice')
        voucher_obj = self.pool.get('account.voucher')
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = (0,0)
            invoice_id = invoice_obj.search(cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
            if invoice_id:
                inv = invoice_obj.browse(cr, uid, invoice_id[0], context)
                if inv.payment_type:
                    result[rec.id] = (inv.payment_type.id, self.pool.get('payment.type').browse(cr, uid, inv.payment_type.id, context).name)
            else:
                voucher_id = voucher_obj.search(cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
                if voucher_id:
                    voucher = voucher_obj.browse(cr, uid, voucher_id[0], context)
                    if voucher.payment_type:
                        result[rec.id] = (voucher.payment_type.id, self.pool.get('payment.type').browse(cr, uid, voucher.payment_type.id, context).name)
                    else:
                        result[rec.id] = (0,0)
                else:
                    result[rec.id] = (0,0)
        return result

#Sin modificaciones del original de momento... hay que hacer que encuentre los heredados del comprobante de cobro
    def _payment_type_search(self, cr, uid, obj, name, args, context={}):
        if not len(args):
            return []
#        operator = args[0][1]
        value = args[0][2]
        if not value:
            return []
        if isinstance(value, int) or isinstance(value, long):
            ids = [value]
        elif isinstance(value, list):
            ids = value 
        else:
            ids = self.pool.get('payment.type').search(cr,uid,[('name','ilike',value)], context=context)
        if ids:
            cr.execute('SELECT l.id ' \
                'FROM account_move_line l, account_invoice i, account_voucher j ' \
                'WHERE (l.move_id = j.move_id AND j.payment_type = ' + str(ids[0]) + ') OR (l.move_id = i.move_id AND i.payment_type in (%s))' % (','.join(map(str, ids))))
            res = cr.fetchall()
            if len(res):
                return [('id', 'in', [x[0] for x in res])]
        return [('id','=','0')]
 
## Se crea un nuevo campo funcional de tipo booleanto que obtiene si es pago corresponde a un efecto de gestión comercial o no.    
    def _indirect_payment_get(self, cr, uid, ids, field_name, arg, context=None):
        result = {}
        voucher_obj = self.pool.get('account.voucher')
        for rec in self.browse(cr, uid, ids, context):
            result[rec.id] = False
            voucher_id = voucher_obj.search(cr, uid, [('move_id', '=', rec.move_id.id)], context=context)
            if voucher_id:
                voucher = voucher_obj.browse(cr, uid, voucher_id[0], context)
                if voucher.indirect_payment:
                    if rec.debit > 0: #rec.id.account_id.type = 'receivable'
                        result[rec.id] = True
                    else:
                        result[rec.id] = False
                else:
                    result[rec.id] = False
            else:
                    result[rec.id] = False
        return result
 
# Creamos los metodos de busqueda para obtener los registros que tienen el check de efecto de gestión comercial marcado   
    def _indirect_payment_search(self, cr, uid, obj, name, args, context={}):
        """ Definition for searching account move lines with indirect_payment check ('indirect_payment','=',True)"""
        for x in args:
            if (x[2] is True) and (x[1] == '=') and (x[0] == 'indirect_payment'):
                cr.execute('SELECT l.id FROM account_move_line l ' \
                    'LEFT JOIN account_voucher i ON l.move_id = i.move_id ' \
                    'WHERE i.indirect_payment = TRUE AND l.debit > 0', []) # NOTA A MEJORAR CUANDO DEBAN INCLUIRSE LOS EFECTOS DE PAGO
                res = cr.fetchall()
                if not len(res):
                    return [('id', '=', '0')]
            elif (x[2] is False) and (x[1] == '=') and (x[0] == 'indirect_payment'):
                cr.execute('SELECT l.id FROM account_move_line l ' \
                    'LEFT JOIN account_voucher i ON l.move_id = i.move_id ' \
                    'WHERE i.indirect_payment = FALSE', []) 
                res = cr.fetchall()
                if not len(res):
                    return [('id', '=', '0')]
        return [('id', 'in', [x[0] for x in res])]
        
    
   
    _columns = {
         'payment_type': fields.function(_payment_type_get, fnct_search=_payment_type_search, method=True, type="many2one", relation="payment.type", string="Payment type"),
         'indirect_payment': fields.function(_indirect_payment_get, fnct_search=_indirect_payment_search, method=True, type="boolean", string="Indirect Payment"),

    }
account_move_line()

#['&','|',('invoice','<>',False), ('indirect_payment','<>',False),('account_id.type','in',['receivable','payable'])]
