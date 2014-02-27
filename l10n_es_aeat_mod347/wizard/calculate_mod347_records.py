# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#    Copyright (C) 2012
#        NaN·tic  (http://www.nan-tic.com) All Rights Reserved
#    Copyright (c) 2012 Acysos S.L. (http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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

__author__ = "Luis Manuel Angueira Blanco (Pexego)"

import threading
import netsvc
import time
import re
from osv import osv

class l10n_es_aeat_mod347_calculate_records(osv.osv_memory):
    _name = "l10n.es.aeat.mod347.calculate_records"
    _description = u"AEAT Model 347 Wizard - Calculate Records"

    def _wkf_calculate_records(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self._calculate_records(cr, uid, ids, context, recalculate=False)

        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report', ids and ids[0], 'calculate', cr)

    # Calculate total invoice without IRPF
    def _calculate_total_invoice(self, cr, uid, ids, context=None):
        invoice = self.pool.get('account.invoice').browse(cr,uid,ids,context)
        amount = invoice.cc_amount_untaxed
        for tax_line in invoice.tax_line:
            if tax_line.name.find('IRPF') == -1:
                amount += tax_line.tax_amount
        return amount

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        if context is None:
            context = {}

        try:

            partner_obj = self.pool.get('res.partner')
            partner_address_obj = self.pool.get('res.partner.address')
            
            invoice_obj = self.pool.get('account.invoice')

            report_obj = self.pool.get('l10n.es.aeat.mod347.report')
            partner_record_obj = self.pool.get('l10n.es.aeat.mod347.partner_record')
            invoice_record_obj = self.pool.get('l10n.es.aeat.mod347.invoice_record')

            report_obj = report_obj.browse(cr, uid, ids and ids[0])

            ##
            ## Change status to 'calculated' and set current calculate date
            report_obj.write({
                'state' : 'calculating',
                'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
            })

            ##
            ## Delete previous partner records
            partner_record_obj.unlink(cr, uid, [r.id for r in report_obj.partner_record_ids])
    
            ##
            ## Get the cash journals (moves on this journals will be considered cash)
            cash_journal_ids = self.pool.get('account.journal').search(cr, uid, [('cash_journal', '=', True)])

            ## Get the fiscal year period ids of the non-special periods
            ## (to ignore closing/opening entries)
            period_ids = [period.id for period in report_obj.fiscalyear_id.period_ids if not period.special]

            ##
            ## We will check every partner with include_in_mod347
            visited_partners = []
            partner_ids = partner_obj.search(cr, uid, [('include_in_mod347', '=', True)])
            for partner in partner_obj.browse(cr, uid, partner_ids):
                if partner.id not in visited_partners:
                    receivable_partner_record = False
                    partner_grouped_cif = []

                    if partner.vat and report_obj.group_by_cif:
                        partner_grouped_cif = partner_obj.search(cr, uid, [('vat','=',partner.vat),('include_in_mod347', '=', True)])
                    else:
                        partner_grouped_cif.append(partner.id)

                    visited_partners.extend(partner_grouped_cif)

                    ##
                    ## Search for invoices
                    #
                    # We will repeat the process for sales and purchases:
                    for invoice_type, refund_type in zip(('out_invoice', 'in_invoice'), ('out_refund', 'in_refund')):
                        #
                        # CHECK THE SALE/PURCHASES INVOICE LIMIT -------------------
                        # (A and B operation keys)
                        #

                        #
                        # Search for invoices to this partner (with account moves).
                        #
                        invoice_ids = invoice_obj.search(cr, uid, [
                                    ('partner_id', 'in', partner_grouped_cif),
                                    ('type', '=', invoice_type),
                                    ('period_id', 'in', period_ids),
                                    ('move_id', '!=', None),
				    ('state', 'not in', ['draft','cancel']),
                                ])
                        refund_ids = invoice_obj.search(cr, uid, [
                                    ('partner_id', 'in', partner_grouped_cif),
                                    ('type', '=', refund_type),
                                    ('period_id', 'in', period_ids),
                                    ('move_id', '!=', None),
				    ('state', 'not in', ['draft','cancel']),
                                ])
                        invoices = invoice_obj.browse(cr, uid, invoice_ids)
                        refunds = invoice_obj.browse(cr, uid, refund_ids)

                        ##
                        ## Calculate the invoiced amount
                        ## Remove IRPF tax for invoice amount
                        invoice_amount = 0
                        for invoice in invoices:
                            invoice_amount += self._calculate_total_invoice(cr, uid, invoice.id, context)

                        refund_amount = 0
                        for invoice in refunds:
                            refund_amount += self._calculate_total_invoice(cr, uid, invoice.id, context)

                        total_amount = invoice_amount - refund_amount

                        ##
                        ## If the invoiced amount is greater than the limit
                        ## we will add an partner record to the report.
                        if total_amount > report_obj.operations_limit:
                            if invoice_type == 'out_invoice':
                                operation_key = 'B' # Note: B = Sale operations
                            else:
                                assert invoice_type == 'in_invoice'
                                operation_key = 'A' # Note: A = Purchase operations

                            #
                            # Get the default invoice address of the partner
                            #
                            address = None
                            address_ids = partner_obj.address_get(cr, uid, [partner.id], ['invoice', 'default'])
                            if address_ids.get('invoice'):
                                address = partner_address_obj.browse(cr, uid, address_ids.get('invoice'))
                            elif address_ids.get('default'):
                                address = partner_address_obj.browse(cr, uid, address_ids.get('default'))

                            #
                            # Get the partner data
                            #
                            partner_vat = partner.vat and re.match(r"([A-Z]{0,2})(.*)", partner.vat).groups()[1]
                            partner_state_code = address.state_id and address.state_id.code or ''
                            partner_country_code = address.country_id and address.country_id.code or ''
                            if partner.vat:
                                partner_country_code, partner_vat = re.match("(ES){0,1}(.*)", partner.vat).groups()

                            # Create the partner record
                            partner_record = partner_record_obj.create(cr, uid, {
                                    'report_id': report_obj.id ,
                                    'operation_key' : operation_key,
                                    'partner_id': partner.id,
                                    'partner_vat': partner_vat,
                                    'representative_vat': '',
                                    'partner_state_code': partner_state_code,
                                    'partner_country_code' : partner_country_code,
                                    'amount': total_amount,
                                })

                            if invoice_type == 'out_invoice':
                                receivable_partner_record = partner_record

                            #
                            # Add the invoices detail to the partner record
                            #
                            for invoice in invoices:
                                amount = self._calculate_total_invoice(cr, uid, invoice.id, context)
                                invoice_record_obj.create(cr, uid, {
                                    'partner_record_id' : partner_record,
                                    'invoice_id': invoice.id,
                                    'date': invoice.date_invoice,
                                    'amount': amount,
                                })
                            for invoice in refunds:
                                amount = self._calculate_total_invoice(cr, uid, invoice.id, context)
                                invoice_record_obj.create(cr, uid, {
                                    'partner_record_id' : partner_record,
                                    'invoice_id': invoice.id,
                                    'date': invoice.date_invoice,
                                    'amount': -amount,
                                })

                    #
                    # Search for payments received in cash from this partner.
                    #
                    if cash_journal_ids:
                        cash_account_move_line_ids = self.pool.get('account.move.line').search(cr, uid, [
                                    ('partner_id', 'in', partner_grouped_cif),
                                    ('account_id', '=', partner.property_account_receivable.id),
                                    ('journal_id', 'in', cash_journal_ids),
                                    ('period_id', 'in', period_ids),
                                ])
                        cash_account_move_lines = self.pool.get('account.move.line').browse(cr, uid, cash_account_move_line_ids)

                        # Calculate the cash amount in report fiscalyear
                        received_cash_amount = sum([line.credit for line in cash_account_move_lines])
                    else:
                        cash_account_move_lines = []
                        received_cash_amount = 0.0

                    #
                    # Add the cash detail to the partner record if over limit
                    #
                    if received_cash_amount > report_obj.received_cash_limit:
                        cash_moves = {}

                        # Group cash move lines by origin operation fiscalyear
                        for move_line_obj in cash_account_move_lines:
                            #FIXME: ugly group by reconciliation invoices, because there isn't any direct relationship between payments and invoice
                            invoices = []
                            if move_line_obj.reconcile_id:
                                for line in move_line_obj.reconcile_id.line_id:
                                    if line.invoice:
                                        invoices.append(line.invoice)
                            elif move_line_obj.reconcile_partial_id:
                                for line in move_line_obj.reconcile_id.line_partial_ids:
                                    if line.invoice:
                                        invoices.append(line.invoice)

                            invoices = list(set(invoices))

                            if invoices:
                                invoice = invoices[0]
                                cash_move_fiscalyear = str(invoice.period_id.fiscalyear_id.id)
                                if cash_move_fiscalyear not in cash_moves:
                                    cash_moves[cash_move_fiscalyear] = [move_line_obj]
                                else:
                                    cash_moves[cash_move_fiscalyear].append(move_line_obj)

                        if cash_moves:
                            for record in cash_moves:
                                partner_rec = False
                                receivable_amount = 0.0
                                receivable_amount = sum([line.credit for line in cash_moves[record]])
                                if receivable_amount > report_obj.received_cash_limit:
                                    if record != str(report_obj.fiscalyear_id.id) or not receivable_partner_record:
                                        #create partner record for cash operation in different year to currently
                                        cash_partner_record = self.pool.get('l10n.es.aeat.mod347.partner_record').create(cr, uid, {
                                                'report_id': report_obj.id ,
                                                'operation_key' : operation_key,
                                                'partner_id': partner.id,
                                                'partner_vat': partner_vat,
                                                'representative_vat': '',
                                                'partner_state_code': partner_state_code,
                                                'partner_country_code' : partner_country_code,
                                                'amount': 0.0,
                                                'cash_amount': sum([line.credit for line in cash_moves[record]]),
                                                'origin_fiscalyear_id': int(record)
                                            })

                                        partner_rec = cash_partner_record
                                    else:
                                        self.pool.get('l10n.es.aeat.mod347.partner_record').write(cr, uid, [receivable_partner_record], {
                                            'cash_amount': sum([line.credit for line in cash_moves[record]]),
                                            'origin_fiscalyear_id': int(record)
                                        })

                                        partner_rec = receivable_partner_record

                                    for line in cash_moves[record]:
                                        self.pool.get('l10n.es.aeat.mod347.cash_record').create(cr, uid, {
                                            'partner_record_id' : partner_rec,
                                            'move_line_id' : line.id,
                                            'date': line.date,
                                            'amount': line.credit,
                                        })

            if recalculate:
                report_obj.write({
                    'state' : 'calculated',
                    'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
                })
        
        except Exception, ex:
            raise

        return True


    def calculation_threading(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        threaded_calculation = threading.Thread(target=self._calculate_records, args=(cr, uid, ids, context))
        threaded_calculation.start()

        return {}

l10n_es_aeat_mod347_calculate_records()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
