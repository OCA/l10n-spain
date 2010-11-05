# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Import operations model 347 engine
#    Copyright (C) 2009 Asr Oss. All Rights Reserved
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

"""
Import operations model 347 engine wizards
"""
__author__ = """Alejandro Sanchez Ramirez Asr Oss - alejandro@asr-oss.com
                Borja López Soilán (Pexego) - borjals@pexego.es"""



import wizard
import pooler
import time
import threading
import sql_db
import re
import netsvc

class wizard_calculate(wizard.interface):
    """
    Wizard to calculates the 347 model report from the OpenERP invoices/payments.
    """

    ############################################################################
    # Forms
    ############################################################################

    _init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculate partner records" colspan="4" width="400">
        <label string="This wizard will calculate the partner operations records of the 347 report." colspan="4"/>
        <label string="" colspan="4"/>
        <label string="It will create records for the next operations:" colspan="4"/>
        <label string="  A - Purchases of goods and services over the limit (1)." colspan="4"/>
        <label string="  B - Sales of goods and services over the limit (1)." colspan="4"/>
        <!-- <label string=" C - Received payments on behalf of third parties over the limit (3)." colspan="4"/> -->
    </form>"""


    _progress_form = '''<?xml version="1.0"?>
    <form string="Calculating partner records" colspan="4" width="400">
        <label string="The calculation may take a while." colspan="4"/>
        <label string="" colspan="4"/>
        <field name="progress" widget="progressbar"/>
    </form>'''

    _progress_fields = {
        'progress': { 'string': 'Progress', 'type':'float' },
    }


    _done_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculation done" colspan="4" width="400">
        <label string="The partner operation records have been calculated." colspan="4"/>
        <label string="" colspan="4"/>
    </form>"""

    _show_exception_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculation failed!" colspan="4" width="400">
        <label string="Error: The calculation operation has failed!" colspan="4"/>
        <label string="" colspan="4"/>
        <separator string="Details"/>
        <field name="exception_text" colspan="4" nolabel="1"/>
    </form>"""

    _show_exception_fields = {
        'exception_text': {'string': 'Exception', 'type':'text' },
    }

    ############################################################################
    # Actions
    ############################################################################

    def _calculate(self, db_name, uid, data, context=None):
        """
        Calculates the 347 model report from the OpenERP invoices/payments data.
        """
        try:
            conn = sql_db.db_connect(db_name)
            cr = conn.cursor()
            pool = pooler.get_pool(cr.dbname)

            report = pool.get('l10n.es.aeat.mod347.report').browse(cr, uid, data['id'], context=context)

            pool.get('l10n.es.aeat.mod347.report').write(cr, uid, data['id'], {
                'state': 'calc',
                'calc_date': time.strftime('%Y-%m-%d %H:%M:%S')
            })

            #
            # Delete the previous partner records
            #
            pool.get('l10n.es.aeat.mod347.partner_record').unlink(cr, uid, [r.id for r in report.partner_records])

            # Get the cash journals (moves on this journals will be considered cash)
            cash_journal_ids = pool.get('account.journal').search(cr, uid, [('cash_journal', '=', True)])

            # Get the fiscal year period ids of the non-special periods
            # (to ignore closing/opening entries)
            period_ids = [period.id for period in report.fiscalyear_id.period_ids if not period.special]

            #
            # We will check every partner with include_in_mod347
            #
            partner_ids = pool.get('res.partner').search(cr, uid, [('include_in_mod347', '=', True)])
            partners_done = 0
            total_partners = len(partner_ids)
            for partner in pool.get('res.partner').browse(cr, uid, partner_ids):

                #
                # Search for invoices
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
                    invoice_ids = pool.get('account.invoice').search(cr, uid, [
                                ('partner_id', '=', partner.id),
                                ('type', '=', invoice_type),
                                ('period_id', 'in', period_ids),
                                ('move_id', '!=', None),
                            ])
                    refund_ids = pool.get('account.invoice').search(cr, uid, [
                                ('partner_id', '=', partner.id),
                                ('type', '=', refund_type),
                                ('period_id', 'in', period_ids),
                                ('move_id', '!=', None),
                            ])
                    invoices = pool.get('account.invoice').browse(cr, uid, invoice_ids)
                    refunds = pool.get('account.invoice').browse(cr, uid, refund_ids)

                    # Calculate the invoiced amount
                    invoice_amount = sum([invoice.cc_amount_total for invoice in invoices])
                    refund_amount = sum([invoice.cc_amount_total for invoice in refunds])
                    total_amount = invoice_amount - refund_amount

                    #
                    # Search for payments received in cash from this partner.
                    #
                    cash_account_move_line_ids = pool.get('account.move.line').search(cr, uid, [
                                ('partner_id', '=', partner.id),
                                ('account_id', '=', partner.property_account_receivable.id),
                                ('journal_id', 'in', cash_journal_ids),
                                ('period_id', 'in', period_ids),
                            ])
                    cash_account_move_lines = pool.get('account.move.line').browse(cr, uid, cash_account_move_line_ids)

                    # Calculate the cash amount
                    received_cash_amount = sum([line.credit for line in cash_account_move_lines])

                    #
                    # If the invoiced amount is greater than the limit
                    # we will add an partner record to the report.
                    #
                    if total_amount > report.operations_limit:
                        if invoice_type == 'out_invoice':
                            operation_key = 'B' # Note: B = Sale operations
                        else:
                            assert invoice_type == 'in_invoice'
                            operation_key = 'A' # Note: A = Purchase operations

                        #
                        # Get the default invoice address of the partner
                        #
                        address = None
                        address_ids = pool.get('res.partner').address_get(cr, uid, [partner.id], ['invoice', 'default'])
                        if address_ids.get('invoice'):
                            address = pool.get('res.partner.address').browse(cr, uid, address_ids.get('invoice'))
                        elif address_ids.get('default'):
                            address = pool.get('res.partner.address').browse(cr, uid, address_ids.get('default'))

                        #
                        # Get the partner data
                        #
                        partner_vat = partner.vat and re.match(r"([A-Z]{0,2})(.*)", partner.vat).groups()[1]
                        partner_state_code = address.state_id and address.state_id.code or ''
                        partner_country_code = address.country_id and address.country_id.code or ''
                        if partner.vat:
                            partner_country_code, partner_vat = re.match("(ES){0,1}(.*)", partner.vat).groups()

                        # Create the partner record
                        partner_record = pool.get('l10n.es.aeat.mod347.partner_record').create(cr, uid, {
                                'report_id': report.id ,
                                'operation_key' : operation_key,
                                'partner_id': partner.id,
                                'partner_vat': partner_vat,
                                'representative_vat': '',
                                'partner_state_code': partner_state_code,
                                'partner_country_code' : partner_country_code,
                                'amount': total_amount,
                                'cash_amount': received_cash_amount > report.received_cash_limit and received_cash_amount or 0,
                            })

                        #
                        # Add the invoices detail to the partner record
                        #
                        for invoice in invoices:
                            pool.get('l10n.es.aeat.mod347.invoice_record').create(cr, uid, {
                                'partner_record_id' : partner_record,
                                'invoice_id': invoice.id,
                                'date': invoice.date_invoice,
                                'amount': invoice.cc_amount_total,
                            })
                        for invoice in refunds:
                            pool.get('l10n.es.aeat.mod347.invoice_record').create(cr, uid, {
                                'partner_record_id' : partner_record,
                                'invoice_id': invoice.id,
                                'date': invoice.date_invoice,
                                'amount': -invoice.cc_amount_total,
                            })

                        #
                        # Add the cash detail to the partner record if over limit
                        #
                        if received_cash_amount > report.received_cash_limit:
                            for line in cash_account_move_lines:
                                pool.get('l10n.es.aeat.mod347.cash_record').create(cr, uid, {
                                    'partner_record_id' : partner_record,
                                    'move_line_id' : line.id,
                                    'date': line.date,
                                    'amount': line.credit,
                                })

                    #
                    # TODO: Calculate records of operation keys C-D-E-F-G !
                    #

                #
                # Update the progress:
                #
                partners_done += 1
                data['calculation_progress'] = (partners_done * 100.0) / total_partners

            #
            # Set the report as calculated
            #
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report', report.id, 'calculate', cr)

            data['calculation_progress'] = 100
            cr.commit()
        except Exception, ex:
            data['calculation_exception'] = ex
            cr.rollback()
            raise
        finally:
            cr.close()
            data['calculation_done'] = True
        return {}


    def _calculate_in_background_choice(self, cr, uid, data, context):
        """
        Choice-like action that runs the calculation on background,
        waiting for it to end or timeout.
        """
        if not data.get('calculation_thread'):
            # Run the calculation in background
            data['calculation_done'] = False
            data['calculation_exception'] = None
            data['calculation_thread'] = threading.Thread(target=self._calculate, args=(cr.dbname, uid, data, context))
            data['calculation_thread'].start()
        #
        # Wait up some seconds seconds for the task to end.
        #
        time_left = 20
        while not data['calculation_done'] and time_left > 0:
            time_left = time_left - 1
            time.sleep(1)
        #
        # Check if we are done
        #
        if data['calculation_done']:
            if data['calculation_exception']:
                return 'show_exception'
            else:
                return 'done'
        else:
            return 'progress'


    def _progress_action(self, cr, uid, data, context):
        """
        Action that gets the current progress
        """
        return { 'progress': data['calculation_progress'] }

    def _show_exception_action(self, cr, uid, data, context):
        """
        Action that gets the calculation exception text
        """
        try:
            exception_text = unicode(data.get('process_exception', ''))
        except UnicodeDecodeError:
            exception_text = str(data.get('process_exception', ''))
        return { 'exception_text': exception_text }

    ############################################################################
    # States
    ############################################################################

    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_form, 'fields': {}, 'state':[('end', 'Cancel', 'gtk-cancel', True), ('calculate_records', 'Calculate', 'gtk-apply', True)]}
        },
        'calculate_records': {
            'actions': [],
            'result': {'type': 'choice', 'next_state': _calculate_in_background_choice}
        },
        'progress': {
            'actions': [_progress_action],
            'result': {'type': 'form', 'arch': _progress_form, 'fields': _progress_fields, 'state':[('end','Close (continues in background)', 'gtk-cancel', True),('calculate_records','Keep waiting', 'gtk-go-forward', True)]}
        },
        'done': {
            'actions': [],
            'result': {'type': 'form', 'arch': _done_form, 'fields': {}, 'state':[('end','Done', 'gtk-ok', True)]}
        },
        'show_exception': {
            'actions': [_show_exception_action],
            'result': {'type': 'form', 'arch': _show_exception_form, 'fields': _show_exception_fields, 'state':[('end','Done', 'gtk-ok', True)]}
        }
    }


wizard_calculate('l10n_es_aeat_mod347.calculate_wizard')

