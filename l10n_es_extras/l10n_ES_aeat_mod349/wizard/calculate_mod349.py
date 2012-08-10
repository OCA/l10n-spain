# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
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

import wizard
import pooler
import time
import threading
import sql_db
import netsvc
import re

vat_regex = re.compile(u"[a-zA-Z]{2}.*", re.UNICODE | re.X)

class wizard_calculate_mod349(wizard.interface):
    """
    Wizard that calculates the result for AEAT 349 Model. There are some facts:
    
    - Operations to declare
        · Intra-Community supplies exempt from VAT, including the transfer of goods to another Member State
        · Intra-Community acquisition subject, including the transfer of goods from another Member State
        · Triangular operations. Subsequent deliveries in other Member States exempt
          intra-Community acquisitions by triangular
        · Adjustments to previous operations, whether returns of supplies or
          intra-Community acquisitions, which have been stated previously in this model
          
    - Operations NOT to declare
        · Supplies of new means of transport for occasional taxpayers
        · Supply of goods whose recipients do not have assigned a TIN / VAT in another Member State
        · Taxable and exempt purchases by triangular
        · NEVER IN THIS MODEL. Services, whether received as effected, with
          businessmen or professionals from other Member States.

    """

    
    #############
    ### FORMS ###
    #############
    INIT_FORM = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculate records" colspan="4" width="500">
        <label string="This wizard will calculate lines for AEAT Model 349."/>
    </form>
    """

    PROGRESS_FORM = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculating partner records" colspan="4" width="500">
        <label string="The calculation of records may take a while.\nThanks for your patience." colspan="4"/>
        <label string="" colspan="4"/>
        <field name="progress" widget="progressbar"/>
    </form>
    """

    DONE_FORM = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculation done" colspan="4" width="400">
        <label string="The records have been calculated succesfully." colspan="4"/>
        <label string="" colspan="4"/>
    </form>"""

    SHOW_EXCEPTION_FORM = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Calculation failed!" colspan="4" width="400">
        <label string="Error: The calculation operation has failed!" colspan="4"/>
        <label string="" colspan="4"/>
        <separator string="Details"/>
        <field name="exception_text" colspan="4" nolabel="1"/>
    </form>"""


    ###################
    ### FORM FIELDS ###
    ###################
    PROGRESS_FIELDS = {
        'progress' : {
            'string' : 'Progress',
            'type' : 'float'
        }
    }

    SHOW_EXCEPTION_FIELDS = {
        'exception_text' : {
            'string' : 'Exception',
            'type' : 'text'
        }
    }


    ###############
    ### ACTIONS ###
    ###############
    def _formatPartnerVAT(self, cr, uid, partner_vat=None, country_id=None):
        """
        Formats VAT to match XXVATNUMBER (where XX is country code)
        """
        if partner_vat and \
            not vat_regex.match(partner_vat) and country_id:
            partner_vat = pooler.get_pool(cr.dbname).get('res.country').browse(cr, uid, country_id[0][0]).code + partner_vat

        return partner_vat

    def _create_partner_records_for_report(self, cr, uid, ids, report_id, partner_obj, operation_key):
        """creates partner records in 349"""
        pool = pooler.get_pool(cr.dbname)
        invoices_ids = pool.get('account.invoice').browse(cr, uid, ids)

        obj = pool.get('l10n.es.aeat.mod349.partner_record')

        partner_country = [address.country_id.id for address in partner_obj.address if address.type == 'invoice' and address.country_id]

        if not len(partner_country):
            partner_country = [address.country_id.id for address in partner_obj.address if address.type == 'default' and address.country_id]

        invoice_created = obj.create(cr, uid, {
            'report_id' : report_id,
            'partner_id' : partner_obj.id,
            'partner_vat' : self._formatPartnerVAT(cr, uid, partner_vat=partner_obj.vat, country_id=partner_country),
            'operation_key' : operation_key,
            'country_id' : partner_country and partner_country[0] or False,
            'total_operation_amount' : sum([invoice.cc_amount_untaxed for invoice in invoices_ids if invoice.type not in ('in_refund', 'out_refund')]) - sum([invoice.cc_amount_untaxed for invoice in invoices_ids if invoice.type in ('in_refund', 'out_refund')])
        })

        ### Creation of partner detail lines
        for invoice in invoices_ids:
            pool.get('l10n.es.aeat.mod349.partner_record_detail').create(cr, uid, {
                'partner_record_id' : invoice_created,
                'invoice_id' : invoice.id,
                'amount_untaxed' : invoice.cc_amount_untaxed
            })

        return invoice_created

    def _create_refund_records_for_report(self, cr, uid, ids, report_id, partner_obj, operation_key):
        """creates restitution records in 349"""
        pool = pooler.get_pool(cr.dbname)
        refunds = pool.get('account.invoice').browse(cr, uid, ids)

        obj = pool.get('l10n.es.aeat.mod349.partner_refund')

        partner_country = [address.country_id.id for address in partner_obj.address if address.type == 'invoice' and address.country_id]

        if not len(partner_country):
            partner_country = [address.country_id.id for address in partner_obj.address if address.type == 'default' and address.country_id]

        record = {}

        for invoice in refunds:
            #goes around all refunded invoices
            for origin_inv in invoice.origin_invoices_ids:
                if origin_inv.state in ['open', 'paid']:
                    #searches for details of another 349s to restor
                    refund_detail = pool.get('l10n.es.aeat.mod349.partner_record_detail').search(cr, uid, [('invoice_id', '=', origin_inv.id)])
                    valid_refund_details = refund_detail
                    for detail in pool.get('l10n.es.aeat.mod349.partner_record_detail').browse(cr, uid, refund_detail):
                        if not detail.partner_record_id.report_id:
                            valid_refund_details.remove(detail.id)

                    if valid_refund_details:
                        rd = pool.get('l10n.es.aeat.mod349.partner_record_detail').browse(cr, uid, valid_refund_details[0])
                        #creates a dictionary key with partner_record id to after recover it
                        key = str(rd.partner_record_id.id)
                        #separates restitutive invoices and nomal, refund invoices of correct period
                        if record.get(key):
                            record[key].append(invoice)
                            #NOTE: Two or more refunded invoices declared in different 349s isn't implemented
                            break
                        else:
                            record[key] = [invoice]
                            #NOTE: Two or more refunded invoices declared in different 349s isn't implemented
                            break

        #recorremos nuestro diccionario y vamos creando registros
        for line in record:
            partner_rec = pool.get('l10n.es.aeat.mod349.partner_record').browse(cr, uid, int(line))

            record_created = obj.create(cr, uid, {
                'report_id' : report_id,
                'partner_id' : partner_obj.id,
                'partner_vat' : self._formatPartnerVAT(cr, uid, partner_vat=partner_obj.vat, country_id=partner_country),
                'operation_key' : operation_key,
                'country_id' : partner_country and partner_country[0] or False,
                'total_operation_amount' :  partner_rec.total_operation_amount - sum([x.cc_amount_untaxed for x in record[line]]),
                'total_origin_amount' : partner_rec.total_operation_amount,
                'period_selection': partner_rec.report_id.period_selection,
                'month_selection': partner_rec.report_id.month_selection,
                'fiscalyear_id': partner_rec.report_id.fiscalyear_id.id
            })

            ### Creation of partner detail lines
            for invoice in record[line]:
                pool.get('l10n.es.aeat.mod349.partner_refund_detail').create(cr, uid, {
                    'refund_id' : record_created,
                    'invoice_id' : invoice.id,
                    'amount_untaxed' : invoice.cc_amount_untaxed
                })

        return True


    def _calculate(self, db_name, uid, data, context=None):
        """
        Function that calculates lines por AEAT 349 Model....
        """
        if context is None:
            context = {}

        try:
            ##
            ## Creation of a new thread for current wizard
            ##
            conn = sql_db.db_connect(db_name)
            cr = conn.cursor()

            pool = pooler.get_pool(cr.dbname)
            partner_facade = pool.get('res.partner')
            invoice_facade = pool.get('account.invoice')

            ### Report facades
            report_facade = pool.get('l10n.es.aeat.mod349.report')
            partner_record_facade = pool.get('l10n.es.aeat.mod349.partner_record')
            partner_refund_facade = pool.get('l10n.es.aeat.mod349.partner_refund')
            
            report_obj = report_facade.browse(cr, uid, data['id'], context=context)
            
            ##
            ## Remove previous partner records and partner refunds in report 
            ##
            partner_record_facade.unlink(cr, uid, [record.id for record in report_obj.partner_record_ids])
            partner_refund_facade.unlink(cr, uid, [refund.id for refund in report_obj.partner_refund_ids])

            partner_ids = partner_facade.search(cr, uid, [])           ## Returns all partners
            partners_done = 0                                          ## Partners done counter
            total_partners = len(partner_ids)                          ## Number of partners
            
            for partner in partner_facade.browse(cr, uid, partner_ids):
                for operation_key in ['E', 'A', 'T', 'S', 'I', 'M', 'H']:
                    ##
                    ## Invoices
                    invoice_ids = invoice_facade._get_invoices_by_type(cr, uid, partner.id,
                        operation_key=operation_key,
                        period_selection=report_obj.period_selection,
                        fiscalyear_id=report_obj.fiscalyear_id.id,
                        period_id=report_obj.period_id.id,
                        month=report_obj.month_selection)

                    # Separates normal invoices of restitutions
                    invoice_ids, refunds_ids = invoice_facade.clean_refund_invoices(cr, uid, invoice_ids, partner.id,
                                    fiscalyear_id=report_obj.fiscalyear_id.id, period_id=report_obj.period_id.id,
                                    month=report_obj.month_selection, period_selection=report_obj.period_selection)

                    ##
                    ## Partner records and partner records detail lines
                    ##
                    if invoice_ids:
                        self._create_partner_records_for_report(cr, uid, invoice_ids, report_obj.id, partner, operation_key)

                    ##
                    ## Refunds records and refunds detail lines
                    ##
                    if refunds_ids:
                        self._create_refund_records_for_report(cr, uid, refunds_ids, report_obj.id, partner, operation_key)
                            
                partners_done += 1
                data['calculation_progress'] = (partners_done * 100.0) / total_partners
                

            ## Advance current report status in workflow            
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n.es.aeat.mod349.report', report_obj.id, 'calculate', cr)

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
        return {'progress': data['calculation_progress']}


    def _show_exception_action(self, cr, uid, data, context):
        """
        Action that gets the calculation exception text
        """
        try:
            exception_text = unicode(data.get('calculation_exception', ''))
        except UnicodeDecodeError:
            exception_text = str(data.get('calculation_exception', ''))
        return {'exception_text': exception_text }


    ##############
    ### STATES ###
    ##############
    states = {
        'init' : {
            'actions' : [],
            'result' : {
                'type' : 'form',
                'arch' : INIT_FORM,
                'fields' : {},
                'state' : [
                    ('end', 'Cancel', 'gtk-cancel'),
                    ('calculate_records', 'Calculate', 'gtk-execute')]
            }
        },
        'calculate_records' : {
            'actions' : [],
            'result' : {
                'type' : 'choice',
                'next_state' : _calculate_in_background_choice
            }
        },
        'progress' : {
            'actions' : [_progress_action],
            'result' : {
                'type' : 'form',
                'arch' : PROGRESS_FORM,
                'fields' : PROGRESS_FIELDS,
                'state' : [
                    ('end', 'Close (continues in background)', 'gtk-cancel', True),
                    ('calculate_records', 'Keep waiting', 'gtk-go-forward', True)
                ]
            }
        },
        'done' : {
            'actions' : [],
            'result' : {
                'type' : 'form',
                'arch' : DONE_FORM,
                'fields' : {},
                'state' : [
                    ('end', 'Done', 'gtk-ok', True)]
            }
        },
        'show_exception' : {
            'actions' : [_show_exception_action],
            'result' : {
                'type' : 'form',
                'arch' : SHOW_EXCEPTION_FORM,
                'fields' : SHOW_EXCEPTION_FIELDS,
                'state' : [
                    ('end', 'Done', 'gtk-ok', True)]
            }
        }
    }

wizard_calculate_mod349('l10n_ES_aeat_mod349.calculate_mod349')
