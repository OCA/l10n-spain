# -*- encoding: latin-1 -*-
##############################################################################
#
# Copyright (c) 2010 - NaN Projectes de proramari lliure S.L.
#                      (http://www.nan-tic.com) All Rights Reserved.
# Copyright (c) 2011 - Acysos S.L. (http://www.acysos.com) All Rights Reserved.
#                      Ignacio Ibeas (ignacio@acysos.com)
#                      Updated payment order reconcile to OpenERP 6.0
#   
# Some code has refactored, original authors:
#                       Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#                       Pexego Sistemas Informáticos. All Rights Reserved
#                       Borja López Soilán <borjals@pexego.es>
# 
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

from osv import fields,osv
from tools.translate import _
import netsvc

import base64
import tempfile

import time
import re
from tools.translate import _


class account_bank_statement_split_line_wizard( osv.osv_memory ):
    _name = 'account.bank.statement.split.line.wizard'

    _columns = {
        'amount':fields.float( 'Amount' )
    }

    def action_split(self, cr, uid, ids, context):
        wizard = self.browse(cr, uid, ids[0], context)
        if wizard.amount:
            self.pool.get('account.bank.statement.line').split_line( cr, uid, context['active_id'], wizard.amount,context)
        return {
            'type': 'ir.actions.act_window_close',
        }

    def action_cancel(self, cr, uid, ids, context=None):
        return {
            'type': 'ir.actions.act_window_close',
        }

account_bank_statement_split_line_wizard()



class account_bank_statement(osv.osv):
    _inherit = 'account.bank.statement'

    def _total_amount(self, cursor, user, ids, name, attr, context=None):
        res_currency_obj = self.pool.get('res.currency')
        res_users_obj = self.pool.get('res.users')
        result = {}
        company_currency_id = res_users_obj.browse(cursor, user, user,context=context).company_id.currency_id.id

        statements = self.browse(cursor, user, ids, context=context)
        for statement in statements:
            amount = 0.0
            for line in statement.line_ids:
                amount += line.amount
            result[statement.id] = amount
        return result

    _columns = {
        'total_amount': fields.function(_total_amount, method=True, string='Total Amount'),
    }

    def _attach_file_to_statement(self, cr, uid, file_contents, statement_id, attachment_name, file_name, context=None):
        """
        Attachs a file to the given bank statement.
        """
        
        #
        # Remove previous statement file attachment (if any)
        #
        ids = self.pool.get('ir.attachment').search(cr, uid, [
                    ('res_id', '=', statement_id),
                    ('res_model', '=', 'account.bank.statement'),
                    ('name', '=', attachment_name),
                ], context=context)
        if ids:
            self.pool.get('ir.attachment').unlink(cr, uid, ids, context)

        #
        # Create the new attachment
        #
        res = self.pool.get('ir.attachment').create(cr, uid, {
                    'name': attachment_name,
                    'datas': file_contents,
                    'datas_fname': file_name,
                    'res_model': 'account.bank.statement',
                    'res_id': statement_id,
                }, context=context)

        return res


account_bank_statement()


class account_bank_statement_line(osv.osv):
    _inherit = 'account.bank.statement.line' 

    _columns = {
        'data_ids': fields.one2many('account.bank.statement.line.data', 'line_id', 'Related Data', readonly=True, help='Data related to the line, usually extracted/imported from a file provided by the bank or another partner.'),
        'search_by': fields.selection( [('all','All'),
                                        ('none','None'),
                                        ('reference_and_amount','Reference and Amount'),
                                        ('vat_and_amount','Vat and Amount'),
                                        ('amount','Amount'),
                                        ('invoice_number','Invoice Number'),
                                        ('invoice_origin','Invoice Origin' ),
                                        ('payment_order','Payment Order' ),
                                        ('bank_statement','Bank Statement'),
                                        ('rules','Statement Line Rules')], 'Search By' )
    }

    _defaults={
        'search_by':lambda *a:'all',
    }

    def split_line( self, cr, uid, id, amount, context ):
        line = self.browse(cr, uid, id, context)
        diff = line.amount - amount
        copy_line = self.copy( cr, uid, id, {
            'amount': diff,
            'voucher_id': False
        }, context=context )
        self.write(cr, uid, [id], {
            'amount': amount,
            'voucher_id': False
        }, context )
        return True

    def button_reconcile_search(self, cr, uid, ids, context):
        self.reconcile_search(cr, uid, ids, context)
        return False

    def reconcile_search( self, cr, uid, ids, context, default_maturity_date=None, max_days=None):
        """
        Tries to find the matching move line to reconcile using line's 'search_by' field.

        It returns a dictionary where keys are the line identifiers and values are booleans indicating if
        a move line was found.
        """
        result = {}
        for line in self.browse(cr, uid, ids, context):

            if line.voucher_id:
                continue

            # Get all move lines already added for reconciliation in the statement
            reconciled_move_line_ids=[]
            for statement_line in line.statement_id.line_ids:
                if statement_line.voucher_id and statement_line.id != line.id:
                    reconciled_move_line_ids += [x.move_line_id.id for x in statement_line.voucher_id.line_ids]
 
            # Get extra information attached to the line
            data = self.pool.get('account.bank.statement.line.data').load_to_dictionary(cr, uid, line.id, context)

            maturity_date = default_maturity_date or line.date
            line_ids = self.search_line2reconcile_by_imported_line( cr, uid, line, data, reconciled_move_line_ids, maturity_date, max_days, context)

            if line_ids: 
                reconcile_line = self.pool.get('account.move.line').browse(cr, uid, line_ids[0], context)
                account_type = 'general'
                if reconcile_line.partner_id:
                    if reconcile_line.partner_id.property_account_receivable == reconcile_line.account_id:
                        account_type = 'customer'
                    else:
                        account_type = 'supplier'

                voucher_id = self.pool.get('account.voucher').create(cr, uid, {
                    'date': line.date,
                    'type': line.amount < 0.0 and 'payment' or 'receipt',
                    'partner_id': reconcile_line.partner_id and reconcile_line.partner_id.id,
                    'journal_id': line.statement_id.journal_id.id,
                    'currency_id': line.statement_id.currency.id,
                    'account_id': reconcile_line.credit > 0.0 and line.statement_id.journal_id.default_credit_account_id.id or line.statement_id.journal_id.default_debit_account_id.id,
                    'period_id': line.statement_id.period_id.id,
                    'company_id': line.statement_id.journal_id.company_id.id,
                    'amount': abs(line.amount),
                }, context)

                for reconcile_line in self.pool.get('account.move.line').browse(cr, uid, line_ids, context):
                    self.pool.get('account.voucher.line').create(cr, uid, {
                        'voucher_id': voucher_id,
                        'account_id': reconcile_line.account_id.id,
                        'move_line_id': reconcile_line.id,
                        'type': line.amount < 0.0 and 'dr' or 'cr',
                        'amount': abs(reconcile_line.debit - reconcile_line.credit),
                    }, context)

                self.write( cr, uid, [line.id], {
                    'voucher_id': voucher_id,
                    'account_id': reconcile_line.account_id.id,
                    'partner_id': reconcile_line.partner_id and reconcile_line.partner_id.id or False,
                    'type': account_type,
                }, context )

            result[line.id] = line_ids and True or False
        return result


    def _get_references( self, cr, uid, line, data, context ):
        if not 'reference' in data:
            if line.search_by != 'all':
                raise osv.except_osv(_('Search by reference error'), _('You cannot search by reference because it seems this line has not been imported from a bank statement file. The system expected a "reference" key in the line with amount %(amount).2f in statement %(statement)s.') % {
                    'amount': line.amount, 
                    'statement': line.statement_id.name,
                })
            return []
        return [ data['reference'] ]

    def _get_vats( self, cr, uid, line, data, context ):
        if not 'vat' in data:
            if line.search_by != 'all':
                raise osv.except_osv(_('Search by VAT error'), _('You cannot search by VAT because it seems this line has not been imported from a bank statement file. The system expected a "vat" key in the line with amount %(amount).2f in statement %(statement)s.') % {
                    'amount': line.amount, 
                    'statement': line.statement_id.name,
                })
            return []
        return [ data['vat'] ]

    def _get_invoice_numbers( self, cr, uid, line, data, context ):
        if not 'invoice_number' in data:
            if line.search_by != 'all':
                raise osv.except_osv(_('Search by invoice error'), _('You cannot search by invoice number because it seems this line has not been imported from a bank statement file. The system expected an "invoice_number" key in the line with amount %(amount).2f in statement %(statement)s.') % {
                    'amount': line.amount, 
                    'statement': line.statement_id.name,
                })
            return []
        return [ data['invoice_number'] ]

    def _get_invoice_origins( self, cr, uid, line, data, context ):
        if not 'invoice_origin' in data:
            if line.search_by != 'all':
                raise osv.except_osv(_('Search by invoice error'), _('You cannot search by invoice origin because it seems this line has not been imported from a bank statement file. The system expected an "invoice_origin" key in the line with amount %(amount).2f in statement %(statement)s.') % {
                    'amount': line.amount, 
                    'statement': line.statement_id.name
                })
            return []
        return [ data['invoice_origin'] ]

    def search_line2reconcile_by_imported_line( self, cr, uid, line, data, reconciled_move_line_ids, maturity_date, max_date_diff, context):
        """
        Returns a list of browse objects.
        """

        move_lines = []

        # Search unconciled entries by line reference and amount.
        if line.search_by in ('reference_and_amount', 'all'):
            for reference in self._get_references( cr, uid, line, data, context ): 
                move_lines = self._find_entry_to_reconcile_by_line_ref_and_amount(cr, uid, line, reference, reconciled_move_line_ids, maturity_date, max_date_diff, context)
                if move_lines:
                    break

        # Search unconciled entries by line VAT number and amount.
        if not move_lines and line.search_by in ('vat_and_amount', 'all'):
            for vat in self._get_vats( cr, uid, line, data, context ): 
                move_lines = self._find_entry_to_reconcile_by_line_vat_number_and_amount(cr, uid, line, vat, reconciled_move_line_ids, maturity_date, max_date_diff, context)
                if move_lines:
                    break

        # Search by invoice number
        if not move_lines and line.search_by in ('invoice_number', 'all'):
            for invoice in self._get_invoice_numbers( cr, uid, line, data, context ): 
                move_lines = self._find_entry_to_reconcile_by_invoice_number(cr, uid, invoice, reconciled_move_line_ids, context)
                if move_lines:
                    break

        # Search by invoice origin
        if not move_lines and line.search_by in ('invoice_origin', 'all'):
            for invoice in self._get_invoice_origins( cr, uid, line, data, context ): 
                move_lines = self._find_entry_to_reconcile_by_invoice_origin(cr, uid, invoice, reconciled_move_line_ids, context)
                if move_lines:
                    break

        if not move_lines and line.search_by in ('bank_statement', 'all'):
            move_lines = self._find_entry_to_reconcile_by_bank_statement(cr, uid, line, reconciled_move_line_ids, context)

            
        # Search by line amount.
        if not move_lines and line.search_by in ('amount', 'all'):
            move_lines = self._find_entry_to_reconcile_by_line_amount(cr, uid, line, reconciled_move_line_ids, maturity_date, max_date_diff, context)


        # Search unreconciled payment orders by amount.
        if not move_lines and line.search_by in ('payment_order', 'all'):
            payment_order = self._find_payment_order_to_reconcile_by_line_amount(cr, uid, line, reconciled_move_line_ids, maturity_date, max_date_diff, context)

            if payment_order:
                for line_id in payment_order.line_ids:
                    reconcile_line = line_id.move_line_id
                    
                    account_type = 'general'
                    if reconcile_line.partner_id:
                        if reconcile_line.partner_id.property_account_receivable == reconcile_line.account_id:
                            account_type = 'customer'
                        else:
                            account_type = 'supplier'
                    
                    voucher_id = self.pool.get('account.voucher').create(cr, uid, {
                        'date': line.date,
                        'type': line_id.amount < 0.0 and 'payment' or 'receipt',
                        'partner_id': reconcile_line.partner_id and reconcile_line.partner_id.id,
                        'journal_id': line.statement_id.journal_id.id,
                        'currency_id': line.statement_id.currency.id,
                        'account_id': reconcile_line.credit > 0.0 and line.statement_id.journal_id.default_credit_account_id.id or line.statement_id.journal_id.default_debit_account_id.id,
                        'period_id': line.statement_id.period_id.id,
                        'company_id': line.statement_id.journal_id.company_id.id,
                        'amount': abs(line_id.amount),
                    }, context)
                    self.pool.get('account.voucher.line').create(cr, uid, {
                        'voucher_id': voucher_id,
                        'account_id': reconcile_line.account_id.id,
                        'move_line_id': reconcile_line.id,
                        'type': line_id.amount < 0.0 and 'dr' or 'cr',
                        'amount': abs(reconcile_line.debit - reconcile_line.credit),
                    }, context)

                    new_line_id = self.copy(cr, uid, line.id, {
                        'account_id': reconcile_line.account_id.id,
                        'partner_id': reconcile_line.partner_id and reconcile_line.partner_id.id or False,
                        'amount': payment_order.type == 'receivable' and line_id.amount or -line_id.amount,
                        'voucher_id': voucher_id,
                        'type': account_type,
                    }, context)
                # Remove current line because all payment order lines have already been created
                self.pool.get('account.bank.statement.line').unlink(cr, uid, [line.id], context)

        # Search by using statement line rules
        if not move_lines and line.search_by in ('rules', 'all'):
            self._process_rules(cr, uid, line, context)
 
        return move_lines 

    def _get_default_partner_account_ids(self, cr, uid, context=None):
        """
        Returns the ids of the default receivable and payable accounts
        for partners.
        """
        model_fields_ids = self.pool.get('ir.model.fields').search(cr, uid, [
                                ('name', 'in', ['property_account_receivable', 'property_account_payable']),
                                ('model', '=', 'res.partner'),
                            ], context=context)
        property_ids = self.pool.get('ir.property').search(cr, uid, [
                            ('fields_id', 'in', model_fields_ids),
                            ('res_id', '=', False),
                        ], context=context)

        account_receivable_id = None
        account_payable_id = None

        for prop in self.pool.get('ir.property').browse(cr, uid, property_ids, context):
            if prop.fields_id.name == 'property_account_receivable':
                account_receivable_id = prop.value_reference.id
            elif prop.fields_id.name == 'property_account_payable':
                account_payable_id = prop.value_reference.id

        return (account_receivable_id, account_payable_id)

    def _process_rules(self, cr, uid, line, context):
            ids = self.pool.get('account.bank.statement.line.rule').search(cr, uid, [], context=context)

            found = False
            for rule in self.pool.get('account.bank.statement.line.rule').browse(cr, uid, ids, context):
                if found:
                    break
                for data in line.data_ids:
                    if data.key != rule.key:
                        continue
                    if not rule.expression in data.value:
                        continue

                    values = {}
                    if rule.account_id:
                        values['account_id'] = rule.account_id.id
                    if rule.partner_id:
                        values['partner_id'] = rule.partner_id.id
                    self.pool.get('account.bank.statement.line').write(cr, uid, [line.id], values, context)
                    found = True
                    break


    def _find_partner_by_line_vat_number(self, cr, uid, vat, context=None):
        """
        Searchs for a partner given the vat number of the line.

        Notes:
        - Depending on the bank, the VAT number may be stored on a diferent
          field. So we will have to test if any of those fields looks like a
          spanish VAT number, and then search for a partner with that VAT.
        - Only works for spanish VAT numbers.
        """
        partner_facade = self.pool.get('res.partner')
        partner = None

        #if partner_facade.check_vat_es( vat.replace(' ', '') ):
        code, number = vat[:2].lower(), vat[2:].replace(' ', '')
        if partner_facade.simple_vat_check( cr, uid, code, number, context):
            partner_ids = partner_facade.search(cr, uid, [
                                    ('vat', 'like', '%s' % vat),
                                    ('active', '=', True),
                                ], context=context)
            if len(partner_ids) == 1:
                # We found a partner with that VAT number
                partner = partner_facade.browse(cr, uid, partner_ids[0], context)
        return partner


    def _get_nearest_move_line(self, lines, maturity_date, max_date_diff=None):
        """
        Find the nearest move_line to a given (maturity) date
        """
        min_diff = max_date_diff
        nearest = None
        if not maturity_date:
            maturity_date = time.time()
        maturity_date_timestamp = time.mktime(time.strptime(maturity_date, '%Y-%m-%d'))
        for line in lines:
            line_date = line.date_maturity or line.date
            if line_date:
                line_timestamp = time.mktime(time.strptime(line_date, '%Y-%m-%d'))
                diff = abs(maturity_date_timestamp-line_timestamp)
                if min_diff is None or diff < min_diff:
                    nearest = line.id
                    min_diff = diff
        return nearest

    def _find_entry_to_reconcile_by_invoice_number(self, cr, uid, number, reconciled_move_line_ids, context):
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('number','ilike',number)], context=context)
        domain = [
            ('account_id.reconcile','=',True),
            ('account_id.type','in',['receivable','payable']),
            ('invoice','in',invoice_ids),
        ]

        if reconciled_move_line_ids:
            domain.append( ('id', 'not in', reconciled_move_line_ids) )

        ids = self.pool.get('account.move.line').search(cr, uid, domain, context=context)
        if ids:
            return [ids[0]]
        return []

    def _find_entry_to_reconcile_by_invoice_origin( self, cr, uid, origin, reconciled_move_line_ids, context):
        invoice_ids = self.pool.get('account.invoice').search(cr, uid, [('origin','ilike',origin)], context=context)
        domain = [
            ('account_id.reconcile','=',True),
            ('account_id.type','in',['receivable','payable']),
            ('invoice','in',invoice_ids),
        ]

        if reconciled_move_line_ids:
            domain.append( ('id', 'not in', reconciled_move_line_ids) )

        ids = self.pool.get('account.move.line').search(cr, uid, domain, context=context)
        if ids:
            return [ids[0]]
        return []

    def _find_entry_to_reconcile_by_bank_statement(self, cr, uid, line, reconciled_move_line_ids, context):
        journal_ids = self.pool.get('account.journal').search(cr, uid, [
            ('default_credit_account_id.reconcile','=',True),
            ('default_debit_account_id.reconcile','=',True),
        ], context=context)

        if not journal_ids:
            return []

        ids = self.pool.get('account.bank.statement').search(cr, uid, [
            ('journal_id','in',journal_ids),
            ('id','!=',line.id),
        ], context=context)

        lines = []
        for statement in self.pool.get('account.bank.statement').browse(cr, uid, ids, context):
            account_ids = (
                statement.journal_id.default_credit_account_id.id, 
                statement.journal_id.default_debit_account_id.id
            )
            # If statement.total_amount == line.amount
            if self.pool.get('res.currency').is_zero(cr, uid, statement.currency, statement.total_amount - line.amount):
                for move_line in statement.move_line_ids:
                    if move_line.reconcile_id:
                        # If any of the lines of the statement has been reconciled it means this is not
                        # the statement we're looking for
                        lines = []
                        break
                    if move_line.account_id.id in account_ids:
                        lines.append( move_line.id )
            if lines:
                break
        return lines

    def _find_entry_to_reconcile_by_line_ref_and_amount(self, cr, uid, line,
            reference, reconciled_move_line_ids, maturity_date, max_date_diff, context=None):
        domain = [
            ('id', 'not in', reconciled_move_line_ids),
            ('ref', '=', reference),
            ('reconcile_id', '=', False),
            ('reconcile_partial_id', '=', False),
            ('account_id.type', 'in', ['receivable', 'payable']),
        ]
        return self._find_entry_by_amount(cr, uid, domain, line.amount,maturity_date,max_date_diff,context )

    def _find_entry_by_amount( self, cr, uid, domain, amount, maturity_date, max_date_diff, context ):
        if amount >= 0:
            domain.append( ('debit', '=', '%.2f' % amount ) )
        else:
            domain.append( ('credit', '=', '%.2f' % -amount ) )

        line_ids = self.pool.get('account.move.line').search(cr, uid, domain, context=context)
        if line_ids:
            lines = self.pool.get('account.move.line').browse(cr, uid, line_ids, context)
            line_id = self._get_nearest_move_line(lines, maturity_date, max_date_diff)
            if line_id:
                return [ line_id ]
        return []

    def _find_entry_to_reconcile_by_line_vat_number_and_amount(self, cr, uid, line, vat, reconciled_move_line_ids, maturity_date, max_date_diff, context=None):
        """
        Searchs for a non-conciled entry given the partner vat number of the line and amount.
        If more than one line is found, and one of the lines has the same
        maturity date or at least the same month, that line is returned.
        """
        partner = line.partner_id and line.partner_id.id or False
        amount = line.amount

        if not partner:
            partner = self._find_partner_by_line_vat_number(cr, uid, vat, context)
            partner = partner and partner.id or None
            
        if partner:
            #
            # Find a line to reconcile from this partner
            #
            domain = [
                ('id', 'not in', reconciled_move_line_ids),
                ('partner_id', '=', partner,),
                ('reconcile_id', '=', False),
                ('reconcile_partial_id', '=', False),
                ('account_id.type', 'in', ['receivable', 'payable']),
            ]
            return self._find_entry_by_amount(cr, uid, domain, amount, maturity_date, max_date_diff, context)

        return []

    def _find_entry_to_reconcile_by_line_amount(self, cr, uid, line, 
            reconciled_move_line_ids, maturity_date, max_date_diff, context=None):
        """
        Search for a non-conciled entry given the line amount.
        """
        domain = [
            ('id', 'not in', reconciled_move_line_ids),
            ('reconcile_id', '=', False),
            ('reconcile_partial_id', '=', False),
            ('account_id.type', 'in', ['receivable', 'payable']),
        ]   
        return self._find_entry_by_amount(cr, uid, domain, line.amount, maturity_date, max_date_diff, context )

    def _find_payment_order_to_reconcile_by_line_amount(self, cr, uid, line, 
            reconciled_move_line_ids, maturity_date, max_date_diff, context=None):
        """
        Searchs for a non-conciled payment order with the same total amount.
        (If more than one order matches None is returned).
        """
        # We require account_payment to be installed
        if not 'payment.order' in self.pool.obj_list():
            return None

        #
        # The total field of the payment orders is a functional field,
        # so we can't use it for searching.
        # Also, browsing all the payment orders would be slow and not scale
        # well. So we just let Postgres do the job.
        #
        # The query will search for orders of the given amount and without
        # reconciled (or partial reconciled) lines
        #
        query = """
                SELECT payment_line.order_id, SUM(payment_line.amount_currency) AS total
                FROM payment_line
                INNER JOIN account_move_line ON (payment_line.move_line_id = account_move_line.id)
                GROUP BY payment_line.order_id
                HAVING SUM(payment_line.amount_currency) = %.2f
                        AND COUNT(account_move_line.reconcile_id) = 0
                        AND COUNT(account_move_line.reconcile_partial_id) = 0
                """

        cr.execute(query % line.amount)
        res = cr.fetchall()

        if len(res) == 1:
            # Only one payment order found, return it
            payment_order = self.pool.get('payment.order').browse(cr, uid, res[0][0], context)
            return payment_order
        return None

account_bank_statement_line()


class account_bank_statement_line_data(osv.osv):
    _name = 'account.bank.statement.line.data'

    _columns = {
        'line_id': fields.many2one('account.bank.statement.line', 'Statement Line', required=True, ondelete='cascade'),
        'key': fields.char('Key', size=256),
        'value': fields.char('Value', size=256, required=False, readonly=False, help=''),
    }

    _sql_constraints = [
        ('data_line_key_value_uniq','unique(line_id,key,value)','Key-value pairs must be unique per statement line.'), 
    ]

    def create_from_dictionary(self, cr, uid, line_id, dictionary, context):
        for key, value in dictionary.iteritems():
            self.create(cr, uid, {
                'line_id': line_id,
                'key': key,
                'value': value,
            }, context)

    def load_to_dictionary(self, cr, uid, line_id, context):
        ids = self.search(cr, uid, [('line_id','=',line_id)], context=context)
        data = {}
        for record in self.browse(cr, uid, ids, context):
            data[record.key] = record.value
        return data

account_bank_statement_line_data()

class account_bank_statement_line_rule(osv.osv):
    _name = 'account.bank.statement.line.rule'
    _rec_name = 'key'
    _order = 'sequence'

    _columns = {
        'company_id': fields.many2one('res.company', 'Company', required=True, ondelete='cascade', help='Company in which this rule should apply.'),
        'sequence': fields.integer('Sequence', required=True, help='Rules will be applied in the order defined by this Sequence and will stop in the first matching rule.'),
        'key': fields.char('Key', size=256, required=True, help='Key in statement line data that should match the given Expression.'),
        'expression': fields.char('Expression', size=500, help='If the value of the given Key contains this Expression, Account and Partner will be used for that statement line.'),
        'account_id': fields.many2one('account.account', 'Account', domain="[('type','!=','view'),('company_id','=',company_id)]", ondelete='cascade', help='Account to be used if expression matches.'),
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade', help='Partner to be used if expression matches'),
    }

    _defaults = {
        'sequence': lambda self, cr, uid, context: 1,
        'company_id': lambda self, cr, uid, context: self.pool.get('res.users').browse(cr, uid, uid, context).company_id.id,
    }

    def _check_company(self, cr, uid, ids):
        for rule in self.browse(cr, uid, ids):
            if rule.account_id and rule.company_id != rule.account_id.company_id:
                raise osv.except_osv(_('Company Check Error'), _("Company for account %(account)s does not match rule's company for rule %(rule)s.") % {
                    'account': rule.account_id.code,
                    'rule': rule.key
                })
        return True
        
    _constraints = [ 
        (_check_company, 'Company Check Error.', ['company_id','account_id']) 
    ]

account_bank_statement_line_rule()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
