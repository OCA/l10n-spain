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
import time
from tools.translate import _
import time
from datetime import datetime

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
            partners = self.pool.get('res.partner')
            
            invoices340 = self.pool.get('l10n.es.aeat.mod340.issued')
            invoices340_rec = self.pool.get('l10n.es.aeat.mod340.received')
            
            mod340.write({
                'state' : 'calculated',
                'calculation_date' : time.strftime('%Y-%m-%d %H:%M:%S')
            })
        
            part_id = mod340.company_id.partner_id.id
            
            part = partners.browse(cr, uid, part_id)
            part_vat=part.vat
            if not part_vat:
                raise osv.except_osv(_(mod340.company_id.partner_id.name), _('This company dont have NIF'))
        
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'l10n.es.aeat.mod347.report', ids and ids[0], 'calculate', cr)
            
            fecha_ini = False
            fecha_fin = False
            
            dec_year =mod340.fiscalyear_id.date_start.split('-')[0]
            
            mod = mod340.period
                
            if mod == '01':
                fecha_ini = datetime.strptime(dec_year+'-1-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-1-31 23:59:59','%Y-%m-%d %H:%M:%S')
                
            if mod == '02':
                if int(dec_year)%4 == 0: 
                    fecha_ini = datetime.strptime(dec_year+'-2-1 0:0:0','%Y-%m-%d %H:%M:%S')
                    fecha_fin = datetime.strptime(dec_year+'-2-29 23:59:59','%Y-%m-%d %H:%M:%S')
                else:
                    fecha_ini = datetime.strptime(dec_year+'-2-1 0:0:0','%Y-%m-%d %H:%M:%S')
                    fecha_fin = datetime.strptime(dec_year+'-2-28 23:59:59','%Y-%m-%d %H:%M:%S')
            
#            if mod == '03':
#                fecha_ini = datetime.strptime(dec_year+'-3-1 0:0:0','%Y-%m-%d %H:%M:%S')
#                fecha_fin = datetime.strptime(dec_year+'-3-31 23:59:59','%Y-%m-%d %H:%M:%S')
            
            if mod == '04':
                fecha_ini = datetime.strptime(dec_year+'-4-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-4-30 23:59:59','%Y-%m-%d %H:%M:%S')
                
            if mod == '05':
                fecha_ini = datetime.strptime(dec_year+'-5-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-5-31 23:59:59','%Y-%m-%d %H:%M:%S')
            
#            if mod == '06':
#                fecha_ini = datetime.strptime(dec_year+'-6-1 0:0:0','%Y-%m-%d %H:%M:%S')
#                fecha_fin = datetime.strptime(dec_year+'-6-30 23:59:59','%Y-%m-%d %H:%M:%S')
            
            if mod == '07':
                fecha_ini = datetime.strptime(dec_year+'-7-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-7-31 23:59:59','%Y-%m-%d %H:%M:%S')
                
            if mod == '08':
                fecha_ini = datetime.strptime(dec_year+'-8-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-8-31 23:59:59','%Y-%m-%d %H:%M:%S')
            
#            if mod == '09':
#                fecha_ini = datetime.strptime(dec_year+'-9-1 0:0:0','%Y-%m-%d %H:%M:%S')
#                fecha_fin = datetime.strptime(dec_year+'-9-30 23:59:59','%Y-%m-%d %H:%M:%S')
                
            if mod == '10':
                fecha_ini = datetime.strptime(dec_year+'-10-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-10-31 23:59:59','%Y-%m-%d %H:%M:%S')
            
            if mod == '11':
                fecha_ini = datetime.strptime(dec_year+'-11-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-11-30 23:59:59','%Y-%m-%d %H:%M:%S')
            
#            if mod == '12':
#                fecha_ini = datetime.strptime(dec_year+'-12-1 0:0:0','%Y-%m-%d %H:%M:%S')
#                fecha_fin = datetime.strptime(dec_year+'-12-31 23:59:59','%Y-%m-%d %H:%M:%S')   
                
            if mod == '1T':
                fecha_ini = datetime.strptime(dec_year+'-1-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-3-31 23:59:59','%Y-%m-%d %H:%M:%S')
                mod='03'
                
            if mod == '2T':
                fecha_ini = datetime.strptime(dec_year+'-4-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-6-30 23:59:59','%Y-%m-%d %H:%M:%S')
                mod='06'
                
            if mod == '3T':
                fecha_ini = datetime.strptime(dec_year+'-7-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-9-30 23:59:59','%Y-%m-%d %H:%M:%S')
                mod='09'
                
            if mod == '4T':
                fecha_ini = datetime.strptime(dec_year+'-10-1 0:0:0','%Y-%m-%d %H:%M:%S')
                fecha_fin = datetime.strptime(dec_year+'-12-31 23:59:59','%Y-%m-%d %H:%M:%S')
                mod='12'
            
            code = '340'+dec_year+''+mod+'0001'
            
            invoice = self.pool.get('account.invoice').search(cr,uid,[('id', '>',0 ),('date_invoice','>', fecha_ini),('date_invoice','<',fecha_fin)])
            
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
            
            for partn in invoice:
                part = self.pool.get('account.invoice').browse(cr, uid, partn)
                if not part.partner_id.vat:
                    raise osv.except_osv(_('La siguiente empresa no tiene asignado nif:'), _(part.partner_id.name))
                
                nif = part.partner_id.vat and re.match(r"([A-Z]{0,2})(.*)", part.partner_id.vat).groups()[1]
                country_code = part.address_invoice_id.country_id.code
                
                values = {
                    'mod340_id': mod340.id,
                    'partner_id':part.partner_id.id,
                    'partner_vat':nif,
                    'representative_vat': '',
                    'partner_country_code' : country_code,
                    'invoice_id':part.id,
                    'base_tax':part.amount_untaxed,
                    'amount_tax':part.amount_tax,
                    'total':part.amount_total
                }

                if part.type=="out_invoice" or part.type=="out_refund":
                    invoice_created = invoices340.create(cr,uid,values)
                    
                if part.type=="in_invoice" or part.type=="in_refund":
                    invoice_created = invoices340_rec.create(cr,uid,values)
                    
                tot_base = tot_base + part.amount_untaxed
                tot_amount = tot_amount + part.amount_tax
                tot_tot = tot_tot + part.amount_total
                
                # Add the invoices detail to the partner record
                for tax_line in part.tax_line:
                    name = tax_line.name
                    account_tax = self.pool.get('account.tax').browse(cr, uid, self.pool.get('account.tax').search(cr, uid, [('name','=',name)], context=context))
                    values = {
                        'name': name,
                        'tax_percentage': account_tax[0].amount,
                        'tax_amount': tax_line.tax_amount,
                        'base_amount': tax_line.base_amount,
                        'invoice_record_id': invoice_created,
                    }
                    if part.type=="out_invoice" or part.type=="out_refund":
                        self.pool.get('l10n.es.aeat.mod340.tax_line_issued').create(cr, uid, values)
                    if part.type=="in_invoice" or part.type=="in_refund":
                        self.pool.get('l10n.es.aeat.mod340.tax_line_received').create(cr, uid, values)
                tot_rec = tot_rec + len(part.tax_line)
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
