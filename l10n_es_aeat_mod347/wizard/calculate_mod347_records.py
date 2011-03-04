# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Informáticos. All Rights Reserved
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


    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        if context is None:
            context = {}

        try:

            partner_facade = self.pool.get('res.partner')
            partner_address_facade = self.pool.get('res.partner.address')
            
            invoice_facade = self.pool.get('account.invoice')

            report_facade = self.pool.get('l10n.es.aeat.mod347.report')
            partner_record_facade = self.pool.get('l10n.es.aeat.mod347.partner_record')
            invoice_record_facade = self.pool.get('l10n.es.aeat.mod347.invoice_record')

            report_obj = report_facade.browse(cr, uid, ids and ids[0])

            ##
            ## Change status to 'calculated' and set current calculate date
            report_facade.write(cr, uid, ids, {
                'state' : 'calculating',
                'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
            })

            ##
            ## Delete previous partner records
            partner_record_facade.unlink(cr, uid, [r.id for r in report_obj.partner_records])
    
            ##
            ## Get the cash journals (moves on this journals will be considered cash)
            cash_journal_ids = self.pool.get('account.journal').search(cr, uid, [('cash_journal', '=', True)])

            ## Get the fiscal year period ids of the non-special periods
            ## (to ignore closing/opening entries)
            period_ids = [period.id for period in report_obj.fiscalyear_id.period_ids if not period.special]

            ##
            ## We will check every partner with include_in_mod347
            partner_ids = partner_facade.search(cr, uid, [('include_in_mod347', '=', True)])
            for partner in partner_facade.browse(cr, uid, partner_ids):
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
                    invoice_ids = invoice_facade.search(cr, uid, [
                                ('partner_id', '=', partner.id),
                                ('type', '=', invoice_type),
                                ('period_id', 'in', period_ids),
                                ('move_id', '!=', None),
                            ])
                    refund_ids = invoice_facade.search(cr, uid, [
                                ('partner_id', '=', partner.id),
                                ('type', '=', refund_type),
                                ('period_id', 'in', period_ids),
                                ('move_id', '!=', None),
                            ])
                    invoices = invoice_facade.browse(cr, uid, invoice_ids)
                    refunds = invoice_facade.browse(cr, uid, refund_ids)

                    ##
                    ## Calculate the invoiced amount
                    invoice_amount = sum([invoice.cc_amount_total for invoice in invoices])
                    refund_amount = sum([invoice.cc_amount_total for invoice in refunds])
                    total_amount = invoice_amount - refund_amount
                    
                    ##
                    ## Search for payments received in cash from this partner.
                    ##
                    cash_account_move_line_ids = self.pool.get('account.move.line').search(cr, uid, [
                                ('partner_id', '=', partner.id),
                                ('account_id', '=', partner.property_account_receivable.id),
                                ('journal_id', 'in', cash_journal_ids),
                                ('period_id', 'in', period_ids),
                            ])
                    cash_account_move_lines = self.pool.get('account.move.line').browse(cr, uid, cash_account_move_line_ids)

                    ##
                    ## Calculate the cash amount
                    received_cash_amount = sum([line.credit for line in cash_account_move_lines])

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
                        address_ids = partner_facade.address_get(cr, uid, [partner.id], ['invoice', 'default'])
                        if address_ids.get('invoice'):
                            address = partner_address_facade.browse(cr, uid, address_ids.get('invoice'))
                        elif address_ids.get('default'):
                            address = partner_address_facade.browse(cr, uid, address_ids.get('default'))

                        #
                        # Get the partner data
                        #
                        partner_vat = partner.vat and re.match(r"([A-Z]{0,2})(.*)", partner.vat).groups()[1]
                        partner_state_code = address.state_id and address.state_id.code or ''
                        partner_country_code = address.country_id and address.country_id.code or ''
                        if partner.vat:
                            partner_country_code, partner_vat = re.match("(ES){0,1}(.*)", partner.vat).groups()

                        # Create the partner record
                        partner_record = partner_record_facade.create(cr, uid, {
                                'report_id': report_obj.id ,
                                'operation_key' : operation_key,
                                'partner_id': partner.id,
                                'partner_vat': partner_vat,
                                'representative_vat': '',
                                'partner_state_code': partner_state_code,
                                'partner_country_code' : partner_country_code,
                                'amount': total_amount,
                                'cash_amount': received_cash_amount > report_obj.received_cash_limit and received_cash_amount or 0,
                            })

                        #
                        # Add the invoices detail to the partner record
                        #
                        for invoice in invoices:
                            invoice_record_facade.create(cr, uid, {
                                'partner_record_id' : partner_record,
                                'invoice_id': invoice.id,
                                'date': invoice.date_invoice,
                                'amount': invoice.cc_amount_total,
                            })
                        for invoice in refunds:
                            invoice_record_facade.create(cr, uid, {
                                'partner_record_id' : partner_record,
                                'invoice_id': invoice.id,
                                'date': invoice.date_invoice,
                                'amount': -invoice.cc_amount_total,
                            })

                        #
                        # Add the cash detail to the partner record if over limit
                        #
                        if received_cash_amount > report_obj.received_cash_limit:
                            for line in cash_account_move_lines:
                                pool.get('l10n.es.aeat.mod347.cash_record').create(cr, uid, {
                                    'partner_record_id' : partner_record,
                                    'move_line_id' : line.id,
                                    'date': line.date,
                                    'amount': line.credit,
                                })


            if recalculate:
                report_facade.write(cr, uid, ids, {
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