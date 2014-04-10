# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2010 Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
#    Copyright (c) 2011 Pexego Sistemas Informáticos. All Rights Reserved
#                       Alberto Luengo Cabanillas <alberto@pexego.es>
#    Copyright (c) 2011 Acysos S.L. All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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

"""
C43 format concepts and extension of the bank statement lines.
"""

from osv import osv
from tools.translate import _

class account_bank_statement_line(osv.osv):
    """
    Extends the bank statement lines to try to set the right reconciliation
    for lines edited by hand.
    """

    _inherit = "account.bank.statement.line"

    def generate_voucher_from_import_wizard(self, cr, uid, statement_id, statement_line, line_ids, context):
        """
            Generate a voucher when conciling lines from an AEB43 extract statement
        """
        line_obj = self.pool.get('account.move.line')
        statement_obj = self.pool.get('account.bank.statement')
        currency_obj = self.pool.get('res.currency')
        voucher_obj = self.pool.get('account.voucher')
        voucher_line_obj = self.pool.get('account.voucher.line')
        statement = statement_obj.browse(cr, uid, statement_id, context=context)

        # for each selected move lines
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            ctx = context.copy()
            #  take the date for computation of currency => use payment date
            ctx['date'] = statement_line.date or line.date
            amount = 0.0

            if line.debit > 0:
                amount = line.debit
            elif line.credit > 0:
                amount = -line.credit

            if line.amount_currency:
                amount = currency_obj.compute(cr, uid, line.currency_id.id,
                    statement.currency.id, line.amount_currency, context=ctx)
            elif (line.invoice and line.invoice.currency_id.id <> statement.currency.id):
                amount = currency_obj.compute(cr, uid, line.invoice.currency_id.id,
                    statement.currency.id, amount, context=ctx)

            context.update({'move_line_ids': [line.id]})
            result = voucher_obj.onchange_partner_id(cr, uid, [], partner_id=line.partner_id.id, journal_id=statement.journal_id.id, amount=abs(amount), currency_id= statement.currency.id, ttype=(amount < 0 and 'payment' or 'receipt'), date=line.date, context=context)
            voucher_res = { 'type':(amount < 0 and 'payment' or 'receipt'),
                            'name': line.name,
                            'partner_id': line.partner_id.id,
                            'journal_id': statement.journal_id.id,
                            'account_id': result.get('account_id', statement.journal_id.default_credit_account_id.id), # improve me: statement.journal_id.default_credit_account_id.id
                            'company_id':statement.company_id.id,
                            'currency_id':statement.currency.id,
                            'date':line.date,
                            'amount':abs(amount),
                            'period_id':statement.period_id.id}
            voucher_id = voucher_obj.create(cr, uid, voucher_res, context=context)

            voucher_line_dict =  {}
            if result['value']['line_ids']:
                for line_dict in result['value']['line_ids']:
                    move_line = line_obj.browse(cr, uid, line_dict['move_line_id'], context)
                    if line.move_id.id == move_line.move_id.id:
                        voucher_line_dict = line_dict
            if voucher_line_dict:
                voucher_line_dict.update({'voucher_id': voucher_id})
                voucher_line_obj.create(cr, uid, voucher_line_dict, context=context)

        return voucher_id


    def onchange_partner_id(self, cr, uid, line_ids, context=None, partner_id=None, ptype=None, amount=None, voucher_id=None, form_date=None):
        """Elimina el precálculo del importe de la línea del extracto bancario
            y propone una conciliación automática si encuentra una."""
        
        move_line_obj = self.pool.get('account.move.line')
        voucher_obj = self.pool.get('account.voucher')
        partner_obj = self.pool.get('res.partner')
        bank_st_line_obj = self.pool.get('account.bank.statement.line')
        if bank_st_line_obj.browse(cr, uid, line_ids):
            current_st_line = bank_st_line_obj.browse(cr, uid, line_ids)[0]
            statement_id = current_st_line.statement_id.id
            res = super(account_bank_statement_line, self).onchange_type(cr, uid, line_ids, partner_id, ptype)
            # devuelve res = {'value': {'amount': balance, 'account_id': account_id}}
            if 'value' in res and 'amount' in res['value']:
                del res['value']['amount']
                
            # Busqueda del apunte por importe con partner
            if partner_id and amount:
                #Actualizamos la cuenta del partner...
                current_partner = partner_obj.browse(cr, uid, partner_id)
                if ptype == 'supplier':
                    res['value']['account_id'] = current_partner.property_account_payable.id
                else:
                    res['value']['account_id'] = current_partner.property_account_receivable.id
    
                domain = [
                    ('reconcile_id', '=', False),
                    ('account_id.type', 'in', ['receivable', 'payable']),
                    ('partner_id', '=', partner_id),
                    ('date', '=', current_st_line.date)
                ]
                if amount >= 0:
                    domain.append( ('debit', '=', '%.2f' % amount) )
                else:
                    domain.append( ('credit', '=', '%.2f' % -amount) )
                line_ids = move_line_obj.search(cr, uid, domain, context=context)
                # Solamente crearemos la conciliacion automatica cuando exista un solo apunte
                # que coincida. Si hay mas de uno el usuario tendra que conciliar manualmente y
                # seleccionar cual de ellos es el correcto.
                res['value']['voucher_id'] = ""
                if len(line_ids) == 1:
                    #Miro si existe ya una propuesta de pago para esa fecha, cantidad, proveedor y estado...
                    saved_voucher_id_list = voucher_obj.search(cr, uid, [('date','=',current_st_line.date), ('amount','=',current_st_line.amount), ('partner_id','=',partner_id), ('state','in', ['draft', 'proforma'])])
                    saved_voucher_id = saved_voucher_id_list and saved_voucher_id_list[0] or None
                    if saved_voucher_id:
                        voucher_id = saved_voucher_id
                    form_voucher_id_list = voucher_obj.search(cr, uid, [('date','=', form_date), ('amount','=',amount), ('partner_id','=',partner_id), ('state','in', ['draft', 'proforma'])])
                    form_voucher_id = form_voucher_id_list and form_voucher_id_list[0] or None
                    if form_voucher_id:
                        voucher_id = form_voucher_id
                    if not saved_voucher_id and not form_voucher_id:
                        voucher_id = bank_st_line_obj.generate_voucher_from_import_wizard(cr, uid, statement_id, current_st_line, line_ids, context)
                    res['value']['voucher_id'] = voucher_id
                elif len(line_ids) > 1:
                    move_lines = move_line_obj.browse(cr, uid, line_ids)
                    str_list = []
                    for line in move_lines:
                        str_list.append("'%s'"%(line.ref or line.name))
                    raise osv.except_osv(_('Beware!'), _("%s moves (%s) found for this date and partner. You'll have to concile this line manually...") %(len(line_ids), ', '.join(str_list)))
            return res


    def _get_references( self, cr, uid, line, data, context ):
        """
        Override function in nan_account_statement_module.
        """

        if not 'conceptos' in data or not 'referencia2' in data:
            if line.search_by != 'all':
                raise osv.except_osv(_('Search by references'), _('You cannot search by reference because it seems this line has not been imported from a bank statement file. The system expected "conceptos" and "referencia2" keys in line of amount %(amount).2f in statement %(statement)s.') % {
                    'amount': line.amount, 
                    'statement': line.statement_id.name
                })
            return []
        return [ data['conceptos'], data['referencia2'] ]

    def _get_vats( self, cr, uid, line, data, context ):
        """
        Override function in nan_account_statement_module.
        """

        if not 'referencia1' in data or not 'conceptos' in data:
            if line.search_by != 'all':
                raise osv.except_osv(_('Search by VAT error'), _('You cannot search by VAT because it seems this line has not been imported from a bank statement file. The system expected "referencia1" and "conceptos" keys in line of amount %(amount).2f in statement %(statement)s.') % {
                    'amount': line.amount, 
                    'statement': line.statement_id.name
                })
            return []
        return [ data['referencia1'][:9] , data['conceptos'][:9], data['conceptos'][21:30] ]

account_bank_statement_line()

class account_bank_statement(osv.osv):
    
    _inherit = "account.bank.statement"
    
    _defaults = {
        'name': lambda self, cr, uid, context=None: \
                self.pool.get('ir.sequence').get(cr, uid, 'account.bank.statement'),
    }

    
    def button_confirm_bank(self, cr, uid, ids, context=None):
        done = []
        obj_seq = self.pool.get('ir.sequence')
        if context is None:
            context = {}

        for st in self.browse(cr, uid, ids, context=context):
            j_type = st.journal_id.type
            company_currency_id = st.journal_id.company_id.currency_id.id
            if not self.check_status_condition(cr, uid, st.state, journal_type=j_type):
                continue

            self.balance_check(cr, uid, st.id, journal_type=j_type, context=context)
            if (not st.journal_id.default_credit_account_id) \
                    or (not st.journal_id.default_debit_account_id):
                raise osv.except_osv(_('Configuration Error !'),
                        _('Please verify that an account is defined in the journal.'))

            for line in st.move_line_ids:
                if line.state <> 'valid':
                    raise osv.except_osv(_('Error !'),
                            _('The account entries lines are not in valid state.'))
            for st_line in st.line_ids:
                if st_line.analytic_account_id:
                    if not st.journal_id.analytic_journal_id:
                        raise osv.except_osv(_('No Analytic Journal !'),_("You have to define an analytic journal on the '%s' journal!") % (st.journal_id.name,))
                if not st_line.amount:
                    continue
                c = {'fiscalyear_id': st.period_id and st.period_id.fiscalyear_id.id or False}
                st_line_number = obj_seq.get_id(cr, uid, st.journal_id.sequence_id.id, context=c)
                self.create_move_from_st_line(cr, uid, st_line.id, company_currency_id, st_line_number, context)

            done.append(st.id)
        return self.write(cr, uid, ids, {'state':'confirm'}, context=context)
    
account_bank_statement()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
