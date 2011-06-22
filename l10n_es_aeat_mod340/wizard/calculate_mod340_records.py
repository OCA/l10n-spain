# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Ting. All Rights Reserved
#    Copyright (c) 2011 Acysos S.L. (http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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

__author__ = "Francisco Pascual González (Ting)"

import threading
import netsvc
import time
import re
from osv import osv
from tools.translate import _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class l10n_es_aeat_mod340_calculate_records(osv.osv_memory):
    _name = "l10n.es.aeat.mod340.calculate_records"
    _description = u"AEAT Model 340 Wizard - Calculate Records"

    def _wkf_calculate_records(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self._calculate_records(cr, uid, ids, context, recalculate=False)
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340', ids and ids[0], 'calculate', cr)

        

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        if context is None:
            context = {}

        try:
            report_obj = self.pool.get('l10n.es.aeat.mod340')
            mod340 = report_obj.browse(cr, uid, ids)[0]
            
            invoices340 = self.pool.get('l10n.es.aeat.mod340.issued')
            invoices340_rec = self.pool.get('l10n.es.aeat.mod340.received')
            
            mod340.write({
                'state' : 'calculated',
                'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
            if not mod340.company_id.partner_id.vat:
                raise osv.except_osv(mod340.company_id.partner_id.name, _('This company dont have NIF'))
        
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report', ids and ids[0], 'calculate', cr)
            
            fecha_ini = False
            fecha_fin = False
            
            dec_year =mod340.fiscalyear_id.date_start.split('-')[0]
            
            mod = mod340.period

            if mod >= '01' and mod <= '12':
                fecha_ini = datetime.strptime('%s-%s-01' % (dec_year, mod), '%Y-%m-%d')
                fecha_fin = fecha_ini + relativedelta(months=+1, days=-1)

            if mod in ('T1', 'T2', 'T3', 'T4'):
                month = ( ( int(mod[0])-1 ) * 3 ) + 1
                fecha_ini = datetime.strptime('%s-%s-01' % (dec_year, month), '%Y-%m-%d')
                fecha_fin = fecha_ini + relativedelta(months=+3, days=-1)
                mod = '%02d' % month

            code = '340'+dec_year+''+mod+'0001'
            
            account_period_id = self.pool.get('account.period').search(cr,uid,[('date_start','=',fecha_ini),('date_stop','=',fecha_fin)])
            
            if not account_period_id:
                raise osv.except_osv(_('El periodo seleccionado no coincide con los periodos del año fiscal:'), dec_year)
            
            
            tot_base = 0
            tot_amount = 0
            tot_tot = 0
            tot_rec = 0
            
            
            #Limpieza de las facturas calculadas anteriormente
            
            del_ids = invoices340.search(cr, uid, [
            ('mod340_id', '=', mod340.id)])

            if del_ids:
                invoices340.unlink(cr, uid, del_ids, context=context)
                
            del_ids = invoices340_rec.search(cr, uid, [
            ('mod340_id', '=', mod340.id)])

            if del_ids:
                invoices340_rec.unlink(cr, uid, del_ids, context=context)
            
            domain = [('period_id', '=',account_period_id[0])]
            # If the system has 'l10n_es_aeat_mod349' module installed, discard
            # invoices with operation_key not null
            if 'operation_key' in self.pool.get('account.invoice')._columns:
                domain += [('operation_key','=',False)]

            invoice_ids = self.pool.get('account.invoice').search(cr, uid, domain, context=context)
            for invoice in self.pool.get('account.invoice').browse(cr, uid, invoice_ids, context):
                if not invoice.partner_id.vat:
                    raise osv.except_osv(_('La siguiente empresa no tiene asignado nif:'), invoice.partner_id.name)
                
                nif = invoice.partner_id.vat and re.match(r"([A-Z]{0,2})(.*)", invoice.partner_id.vat).groups()[1]
                country_code = invoice.address_invoice_id.country_id.code
                
                values = {
                    'mod340_id': mod340.id,
                    'partner_id':invoice.partner_id.id,
                    'partner_vat':nif,
                    'representative_vat': '',
                    'partner_country_code' : country_code,
                    'invoice_id':invoice.id,
                    'base_tax':invoice.amount_untaxed,
                    'amount_tax':invoice.amount_tax,
                    'total':invoice.amount_total
                }

                if invoice.type=="out_invoice" or invoice.type=="out_refund":
                    invoice_created = invoices340.create(cr,uid,values)
                    
                if invoice.type=="in_invoice" or invoice.type=="in_refund":
                    invoice_created = invoices340_rec.create(cr,uid,values)
                
                tot_tax_invoice = 0
                
                # Add the invoices detail to the partner record
                for tax_line in invoice.tax_line:
                    if tax_line.name.find('IRPF') == -1: # Remove IRPF from Mod340
                        tax_description = tax_line.name.split(' - ')
                        if len(tax_description) == 2: name = tax_description[1]
                        if len(tax_description) == 1: name = tax_description[0]
                        account_tax = self.pool.get('account.tax').browse(cr, uid, self.pool.get('account.tax').search(cr, uid, [('name','=',name)], context=context))
                        values = {
                            'name': name,
                            'tax_percentage': account_tax[0].amount,
                            'tax_amount': tax_line.tax_amount,
                            'base_amount': tax_line.base_amount,
                            'invoice_record_id': invoice_created,
                        }
                        if invoice.type=="out_invoice" or invoice.type=="out_refund":
                            self.pool.get('l10n.es.aeat.mod340.tax_line_issued').create(cr, uid, values)
                        if invoice.type=="in_invoice" or invoice.type=="in_refund":
                            self.pool.get('l10n.es.aeat.mod340.tax_line_received').create(cr, uid, values)
                        tot_tax_invoice += tax_line.tax_amount
                        tot_rec += 1
                        
                tot_base += invoice.amount_untaxed
                tot_amount += tot_tax_invoice
                tot_tot += invoice.amount_untaxed + tot_tax_invoice
            
                if invoice.type=="out_invoice" or invoice.type=="out_refund":
                    invoices340.write(cr,uid,invoice_created,{'amount_tax':tot_tax_invoice})
                if invoice.type=="in_invoice" or invoice.type=="in_refund":
                    invoices340_rec.write(cr,uid,invoice_created,{'amount_tax':tot_tax_invoice})
                
            mod340.write({'total_taxable':tot_base,'total_sharetax':tot_amount,'number_records':tot_rec,'total':tot_tot,'number':code})
            
            if recalculate:
                mod340.write({
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

l10n_es_aeat_mod340_calculate_records()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
