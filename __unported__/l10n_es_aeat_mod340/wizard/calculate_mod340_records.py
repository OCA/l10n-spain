# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Ting. All Rights Reserved
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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

import threading
from openerp import netsvc
import time
import re
from openerp.tools.translate import _
from openerp.osv import orm
from datetime import datetime
from dateutil.relativedelta import relativedelta

class l10n_es_aeat_mod340_calculate_records(orm.TransientModel):
    _name = "l10n.es.aeat.mod340.calculate_records"
    _description = u"AEAT Model 340 Wizard - Calculate Records"

    def _wkf_calculate_records(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        self._calculate_records(cr, uid, ids, context, recalculate=False)
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340.report', 
                                ids and ids[0], 'calculate', cr)

        

    def _calculate_records(self, cr, uid, ids, context=None, recalculate=True):
        if context is None:
            context = {}

        try:
            report_obj = self.pool.get('l10n.es.aeat.mod340.report')
            mod340 = report_obj.browse(cr, uid, ids)[0]
            
            invoices340 = self.pool.get('l10n.es.aeat.mod340.issued')
            invoices340_rec = self.pool.get('l10n.es.aeat.mod340.received')
            period_obj = self.pool.get('account.period')
            
            mod340.write({
                'state' : 'calculated',
                'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
            if not mod340.company_id.partner_id.vat:
                raise orm.except_orm(mod340.company_id.partner_id.name,
                                     _('This company dont have NIF'))
        
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report',
                                    ids and ids[0], 'calculate', cr)

            code = '340' + mod340.fiscalyear_id.code + ''
            code += mod340.period_to.date_stop[5:7] + '0001'
            
            account_period_ids = period_obj.build_ctx_periods(cr, uid,
                                  mod340.period_from.id, mod340.period_to.id)

            if len(account_period_ids) == 0:
                raise orm.except_orm(_('Error'),
                   _("The periods selected don't belong to the fiscal year %s") 
                   % (mod340.fiscalyear_id.name))
            
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
            
            domain = [('period_id', 'in',account_period_ids), 
                ('state', 'in', ('open', 'paid'))]
            
            invoice_obj=self.pool.get('account.invoice')
            invoice_ids = invoice_obj.search(cr, uid,domain, context=context)
            for invoice in invoice_obj.browse(cr, uid, invoice_ids, context):
                include = False
                for tax_line in invoice.tax_line:
                    if tax_line.base_code_id and tax_line.base:
                        if tax_line.base_code_id.mod340 == True:
                            include = True
                if include == True:
                    if invoice.partner_id.vat_type == 1:
                        if not invoice.partner_id.vat:
                            raise orm.except_orm(
                              _('La siguiente empresa no tiene asignado nif:'),
                              invoice.partner_id.name)
                    
                    nif = invoice.partner_id.vat and \
                        re.match(r"([A-Z]{0,2})(.*)",
                                 invoice.partner_id.vat).groups()[1]
                    country_code = invoice.partner_id.country_id.code
                    
                    values = {
                        'mod340_id': mod340.id,
                        'partner_id': invoice.partner_id.id,
                        'partner_vat': nif,
                        'representative_vat': '',
                        'partner_country_code': country_code,
                        'invoice_id': invoice.id,
                        'base_tax': invoice.amount_untaxed,
                        'amount_tax': invoice.amount_tax,
                        'total': invoice.amount_total,
                        'date_invoice': invoice.date_invoice,
                    }
                    if invoice.type in ( 'out_refund','in_refund'):
                        values['base_tax'] *= -1
                        values['amount_tax'] *= -1
                        values['total'] *= -1
    
                    
                    if invoice.type=="out_invoice" or invoice.type=="out_refund":
                        invoice_created = invoices340.create(cr,uid,values)
                        
                    if invoice.type=="in_invoice" or invoice.type=="in_refund":
                        invoice_created = invoices340_rec.create(cr,uid,values)
                    
                    tot_tax_invoice = 0
                    check_tax = 0
                    check_base = 0
                    
                    # Add the invoices detail to the partner record
                    for tax_line in invoice.tax_line:
                        if tax_line.base_code_id and tax_line.base:
                            if tax_line.base_code_id.mod340 == True:
                                tax_percentage = tax_line.amount/tax_line.base
        
                                values = {
                                    'name': tax_line.name,
                                    'tax_percentage': tax_percentage,
                                    'tax_amount': tax_line.tax_amount,
                                    'base_amount': tax_line.base_amount,
                                    'invoice_record_id': invoice_created,
                                }
                                if invoice.type=="out_invoice" or invoice.type=="out_refund":
                                    issued_obj = self.pool.get('l10n.es.aeat.mod340.tax_line_issued')
                                    issued_obj.create(cr, uid, values)
                                if invoice.type=="in_invoice" or invoice.type=="in_refund":
                                    received_obj = self.pool.get('l10n.es.aeat.mod340.tax_line_received')
                                    received_obj.create(cr, uid, values)
                                tot_tax_invoice += tax_line.tax_amount
                                tot_rec += 1
                                check_tax += tax_line.tax_amount
                                if tax_percentage >= 0:
                                    check_base += tax_line.base_amount
                                                            
                    tot_base += invoice.amount_untaxed
                    tot_amount += tot_tax_invoice
                    tot_tot += invoice.amount_untaxed + tot_tax_invoice
                
                    if invoice.type == "out_invoice" or invoice.type == "out_refund":
                        invoices340.write(cr,uid,invoice_created,
                                          {'amount_tax':tot_tax_invoice})
                    if invoice.type == "in_invoice" or invoice.type == "in_refund":
                        invoices340_rec.write(cr,uid,invoice_created,
                                              {'amount_tax':tot_tax_invoice})
    
                    sign=1
                    if  invoice.type in ( 'out_refund','in_refund' ):
                        sign = -1
                        
                    if str(invoice.amount_untaxed*sign) != str(check_base):
                        raise orm.except_orm( "REVIEW INVOICE",
                          _('Invoice  %s, Amount untaxed Lines %.2f do not correspond to AmountUntaxed on Invoice %.2f' )
                          %(invoice.number, check_base,  
                            invoice.amount_untaxed*sign)  )
                
            mod340.write({'total_taxable':tot_base,'total_sharetax':tot_amount,
                      'number_records':tot_rec,'total':tot_tot,
                      'declaration_number':code})
            
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

        threaded_calculation = threading.Thread(target=self._calculate_records,
                                                args=(cr, uid, ids, context))
        threaded_calculation.start()

        return {}
