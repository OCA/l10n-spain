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

import threading
import time
import netsvc
import re
from osv import osv

vat_regex = re.compile(u"[a-zA-Z]{2}.*", re.UNICODE | re.X)

class l10n_es_aeat_mod349_calculate_records(osv.osv_memory):
    _name = "l10n.es.aeat.mod349.calculate_records"
    _description = u"AEAT Model 349 Wizard - Calculate Records"
    

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
        invoices_ids = self.pool.get('account.invoice').browse(cr, uid, ids)

        obj = self.pool.get('l10n.es.aeat.mod349.partner_record')

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
            self.pool.get('l10n.es.aeat.mod349.partner_record_detail').create(cr, uid, {
                'partner_record_id' : invoice_created,
                'invoice_id' : invoice.id,
                'amount_untaxed' : invoice.cc_amount_untaxed
            })

        return invoice_created

    def _create_refund_records_for_report(self, cr, uid, ids, report_id, partner_obj, operation_key):
        """creates restitution records in 349"""
        refunds = self.pool.get('account.invoice').browse(cr, uid, ids)

        obj = self.pool.get('l10n.es.aeat.mod349.partner_refund')

        partner_country = [address.country_id.id for address in partner_obj.address if address.type == 'invoice' and address.country_id]
        if not len(partner_country):
            partner_country = [address.country_id.id for address in partner_obj.address if address.type == 'default' and address.country_id]

        record = {}

        for invoice in refunds:
            #goes around all refunded invoices
            for origin_inv in invoice.origin_invoices_ids:
                if origin_inv.state in ['open', 'paid']:
                    #searches for details of another 349s to restor
                    refund_detail = self.pool.get('l10n.es.aeat.mod349.partner_record_detail').search(cr, uid, [('invoice_id', '=', origin_inv.id)])
                    valid_refund_details = refund_detail
                    for detail in self.pool.get('l10n.es.aeat.mod349.partner_record_detail').browse(cr, uid, refund_detail):
                        if not detail.partner_record_id.report_id:
                            valid_refund_details.remove(detail.id)
                    
                    if valid_refund_details:
                        rd = self.pool.get('l10n.es.aeat.mod349.partner_record_detail').browse(cr, uid, valid_refund_details[0])
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
            partner_rec = self.pool.get('l10n.es.aeat.mod349.partner_record').browse(cr, uid, int(line))

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
                self.pool.get('l10n.es.aeat.mod349.partner_refund_detail').create(cr, uid, {
                    'refund_id' : record_created,
                    'invoice_id' : invoice.id,
                    'amount_untaxed' : invoice.cc_amount_untaxed
                })

        return True

    def _wkf_calculate_records(self, cr, uid, ids, context=None):
        """moves forward workflow"""
        if context is None:
            context = {}
            
        self._calculate_records(cr, uid, ids, context, recalculate=False)

        ##
        ## Advance current report status in workflow
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod349.report', ids and ids[0], 'calculate', cr)
        

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        """computes the records in report"""
        if context is None:
            context = {}

        try:
            partner_obj = self.pool.get('res.partner')
            invoice_obj = self.pool.get('account.invoice')

            report_obj = self.pool.get('l10n.es.aeat.mod349.report')
            partner_record_obj = self.pool.get('l10n.es.aeat.mod349.partner_record')
            partner_refund_obj = self.pool.get('l10n.es.aeat.mod349.partner_refund')

            ##
            ## Remove previous partner records and parter refunds in 349 report
            reports = report_obj.browse(cr, uid, ids and ids[0], context=context)

            report_obj.write(cr, uid, ids, {
                'state' : 'calculating',
                'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
            })

            ##
            ## Remove previous partner records and partner refunds in report
            ##
            partner_record_obj.unlink(cr, uid, [record.id for record in reports.partner_record_ids])
            partner_refund_obj.unlink(cr, uid, [refund.id for refund in reports.partner_refund_ids])

            partner_ids = partner_obj.search(cr, uid, [])           ## Returns all partners

            for partner in partner_obj.browse(cr, uid, partner_ids):
                
                for operation_key in ['E', 'A', 'T', 'S', 'I']:
                    ##
                    ## Invoices
                    invoice_ids = invoice_obj._get_invoices_by_type(cr, uid, partner.id,
                        operation_key=operation_key,
                        period_selection=reports.period_selection,
                        fiscalyear_id=reports.fiscalyear_id.id,
                        period_id=reports.period_id.id,
                        month=reports.month_selection)

                    # Separates normal invoices of restitutions
                    invoice_ids, refunds_ids = invoice_obj.clean_refund_invoices(cr, uid, invoice_ids, partner.id,
                                    fiscalyear_id=reports.fiscalyear_id.id, period_id=reports.period_id.id,
                                    month=reports.month_selection, period_selection=reports.period_selection)

                    ##
                    ## Partner records and partner records detail lines
                    ##
                    if invoice_ids:
                        self._create_partner_records_for_report(cr, uid, invoice_ids, reports.id, partner, operation_key)

                    ##
                    ## Refunds records and refunds detail lines
                    ##
                    if refunds_ids:
                        self._create_refund_records_for_report(cr, uid, refunds_ids, reports.id, partner, operation_key)

            if recalculate:
                report_obj.write(cr, uid, ids, {
                    'state' : 'calculated',
                    'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
                })
            
        except Exception, ex:
            raise

        return {}


    def calculation_threading(self, cr, uid, ids, context=None):
        """manages threading"""
        if context is None:
            context = {}

        threaded_calculation = threading.Thread(target=self._calculate_records, args=(cr, uid, ids, context))
        threaded_calculation.start()

        return {}

l10n_es_aeat_mod349_calculate_records()
