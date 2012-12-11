# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

import netsvc
from osv import fields, osv

class account_invoice(osv.osv):
    _inherit='account.invoice'
    _columns={
        'payment_type': fields.many2one('payment.type', 'Payment type'),
    }

    def onchange_partner_id(self, cr, uid, ids, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        # Copy partner data to invoice, also the new field payment_type
        result = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        payment_type = False
        if partner_id:
            partner_line = self.pool.get('res.partner').browse(cr, uid, partner_id)
            if partner_line:
                if type=='in_invoice' or type=='in_refund':
                    payment_type = partner_line.payment_type_supplier.id
                else:
                    payment_type = partner_line.payment_type_customer.id
            if payment_type:
                result['value']['payment_type'] = payment_type
        return self.onchange_payment_type(cr, uid, ids, payment_type, partner_id, result)

    def onchange_payment_type(self, cr, uid, ids, payment_type, partner_id, result = None):
        if result is None:
            result = {'value': {}}
        if payment_type and partner_id:
            bank_types = self.pool.get('payment.type').browse(cr, uid, payment_type).suitable_bank_types
            if bank_types: # If the payment type is related with a bank account
                bank_types = [bt.code for bt in bank_types]
                partner_bank_obj = self.pool.get('res.partner.bank')
                args = [('partner_id', '=', partner_id), ('default_bank', '=', 1), ('state', 'in', bank_types)]
                bank_account_id = partner_bank_obj.search(cr, uid, args)
                if bank_account_id:
                    result['value']['partner_bank_id'] = bank_account_id[0]
                    return result
        result['value']['partner_bank_id'] = False
        return result

    def action_move_create(self, cr, uid, ids, *args):
        ret = super(account_invoice, self).action_move_create(cr, uid, ids, *args)
        if ret:
            for inv in self.browse(cr, uid, ids):
                move_line_ids = []
                for move_line in inv.move_id.line_id:
                    if (move_line.account_id.type == 'receivable' or move_line.account_id.type == 'payable') and move_line.state != 'reconciled' and not move_line.reconcile_id.id:
                        move_line_ids.append(move_line.id)
                if len(move_line_ids) and inv.partner_bank_id:
                    aml_obj = self.pool.get("account.move.line")
                    aml_obj.write(cr, uid, move_line_ids, {'partner_bank_id': inv.partner_bank_id.id})
        return ret

    def refund(self, cr, uid, ids, date=None, period_id=None, description=None, journal_id=None):
        invoices = self.read(cr, uid, ids, ['name', 'type', 'number', 'reference', 'comment', 'date_due', 'partner_id', 'address_contact_id', 'address_invoice_id', 'partner_contact', 'partner_insite', 'partner_ref', 'payment_term', 'account_id', 'currency_id', 'invoice_line', 'tax_line', 'journal_id', 'payment_type'])
        obj_invoice_line = self.pool.get('account.invoice.line')
        obj_invoice_tax = self.pool.get('account.invoice.tax')
        obj_journal = self.pool.get('account.journal')
        new_ids = []
        for invoice in invoices:
            del invoice['id']

            type_dict = {
                'out_invoice': 'out_refund', # Customer Invoice
                'in_invoice': 'in_refund',   # Supplier Invoice
                'out_refund': 'out_invoice', # Customer Refund
                'in_refund': 'in_invoice',   # Supplier Refund
            }

            invoice_lines = obj_invoice_line.read(cr, uid, invoice['invoice_line'])
            invoice_lines = self._refund_cleanup_lines(cr, uid, invoice_lines)

            tax_lines = obj_invoice_tax.read(cr, uid, invoice['tax_line'])
            tax_lines = filter(lambda l: l['manual'], tax_lines)
            tax_lines = self._refund_cleanup_lines(cr, uid, tax_lines)
            if journal_id:
                refund_journal_ids = [journal_id]
            elif invoice['type'] == 'in_invoice':
                refund_journal_ids = obj_journal.search(cr, uid, [('type','=','purchase_refund')])
            else:
                refund_journal_ids = obj_journal.search(cr, uid, [('type','=','sale_refund')])

            if not date:
                date = time.strftime('%Y-%m-%d')
            invoice.update({
                'type': type_dict[invoice['type']],
                'date_invoice': date,
                'state': 'draft',
                'number': False,
                'invoice_line': invoice_lines,
                'tax_line': tax_lines,
                'journal_id': refund_journal_ids
            })
            if period_id:
                invoice.update({
                    'period_id': period_id,
                })
            if description:
                invoice.update({
                    'name': description,
                })
            # take the id part of the tuple returned for many2one fields
            for field in ('address_contact_id', 'address_invoice_id', 'partner_id',
                    'account_id', 'currency_id', 'payment_term', 'journal_id', 'payment_type'):
                invoice[field] = invoice[field] and invoice[field][0]
            # create the new invoice
            new_ids.append(self.create(cr, uid, invoice))

        return new_ids

account_invoice()
