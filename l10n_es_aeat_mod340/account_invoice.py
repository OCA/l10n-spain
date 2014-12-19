# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2012 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools.float_utils import float_round


class account_invoice(orm.Model):
    _inherit = 'account.invoice'

    def get_340_classification(self, cr, uid, invoice_id, context=None):
        invoice = self.browse(cr, uid, invoice_id, context)
        if invoice.is_ticket_summary:
            return 'E', 'B'
        # Intentamos determinar la clasificación primero en función de la línea de más importe
        max_line = max(invoice.invoice_line, key=lambda x: abs(x.price_subtotal))
        taxes = filter(lambda x: x.ledger_key and x.operation_key != '-', max_line.invoice_line_tax_id)
        if taxes:
            return taxes[0].ledger_key, (taxes[0].operation_key or ' ')
        # y si no cualquier otra
        for line in invoice.invoice_line:
            taxes = filter(lambda x: x.ledger_key and x.operation_key != '-', line.invoice_line_tax_id)
            if taxes:
                return taxes[0].ledger_key, (taxes[0].operation_key or ' ')
        raise orm.except_orm(
            'Error',
            'No se pudo determinar la clasificacion de la factura %s porque sus impuestos no se declaran en el modelo 340' % invoice.number)

    def get_inv_good_names(self, cr, uid, invoice_id, tax_percentage, context=None):
        names = []
        invoice = self.browse(cr, uid, invoice_id, context)
        tax_percentage = abs(tax_percentage)
        for line in invoice.invoice_line:
            for tax in line.invoice_line_tax_id:
                if tax.ledger_key in ('I', 'J') and tax.amount == tax_percentage:
                    names.append(line.name)
                    break
        return ', '.join(names)

    def get_cc_amounts(self, cr, uid, invoice_id, context=None):
        # Créditos Zikzakmedia SL @ account_invoice_currency
        invoice = self.browse(cr, uid, invoice_id, context)
        if invoice.company_id.currency_id == invoice.currency_id:
            return {
                'cc_amount_untaxed': invoice.amount_untaxed,
                'cc_amount_tax': invoice.amount_tax,
                'cc_amount_total': invoice.amount_total,
            }

        res = {
            'cc_amount_untaxed': 0.0,
            'cc_amount_tax': 0.0,
            'cc_amount_total': 0.0,
        }

        ## It could be computed only in open or paid invoices with a generated account move
        if invoice.move_id:
            precision = self.pool.get('decimal.precision').precision_get(cr, uid, 'Account')
            ## Accounts to compute amount_untaxed
            line_account = []
            for line in invoice.invoice_line:
                if line.account_id.id not in line_account:
                    line_account.append(line.account_id.id)

            ## Accounts to compute amount_tax
            tax_account = []
            for line in invoice.tax_line:
                if line.account_id.id not in tax_account and line.amount != 0:
                    tax_account.append(line.account_id.id)

            ## The company currency amounts are the debit-credit amounts in the account moves
            for line in invoice.move_id.line_id:
                if line.account_id.id in line_account:
                    res['cc_amount_untaxed'] += float_round(line.debit - line.credit, precision)
                if line.account_id.id in tax_account:
                    res['cc_amount_tax'] += float_round(line.debit - line.credit, precision)
            if invoice.type in ('out_invoice', 'in_refund'):
                res['cc_amount_untaxed'] = -res['cc_amount_untaxed']
                res['cc_amount_tax'] = -res['cc_amount_tax']
            res['cc_amount_total'] = res['cc_amount_tax'] + res['cc_amount_untaxed']
        return res

    _columns = {
        'is_ticket_summary': fields.boolean(
            'Ticket Summary', help='Check if this invoice is a ticket summary'),
        'number_tickets': fields.integer('Number of tickets', digits=(12, 0)),
        'first_ticket': fields.char('First ticket', size=40),
        'last_ticket': fields.char('Last ticket', size=40)
    }


class account_tax(orm.Model):
    _inherit = "account.invoice.tax"

    def compute(self, cr, uid, invoice_id, context=None):
        tax_obj = self.pool['account.tax']
        res = super(account_tax, self).compute(cr, uid, invoice_id, context)
        for tax_line in res.values():
            name = tax_line['name'].split(' - ')
            tax_id = tax_obj.search(
                cr, uid, ['|', ('name', 'in', name),
                          ('description', 'in', name)],
                context=context)
            if not tax_id:
                raise orm.except_orm(_('Error'),
                                     _('Tax %s not found') % name[1])
            tax_line['tax_id'] = tax_id[0]
        return res

    _columns = {
        'tax_id': fields.many2one('account.tax', "Tax")
    }
