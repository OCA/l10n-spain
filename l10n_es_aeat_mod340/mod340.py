# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
#    Copyright (c) 2011 Acysos S.L. (http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
#                   
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

from osv import osv,fields
import time
from datetime import datetime
import netsvc
import tools
import math
from tools.translate import _
import pooler

class l10n_es_aeat_mod340(osv.osv):
   
    def button_calculate(self, cr, uid, ids,  args, context=None):
        
        if not context:
            context = {}

        calculate_obj = self.pool.get('l10n.es.aeat.mod340.calculate_records')
        calculate_obj._wkf_calculate_records(cr, uid, ids, context)   
        
        
        return True
    
    def button_recalculate(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        calculate_obj = self. pool.get('l10n.es.aeat.mod340.calculate_records')
        calculate_obj._calculate_records(cr, uid, ids, context)

        return True

    def button_export(self, cr, uid, ids, context=None):
        
        if context is None:
            context = {}

        export_obj = self.pool.get("l10n.es.aeat.mod340.export_to_boe")
        report = self.browse(cr, uid, ids and ids[0])
        if report.period_from == report.period_to:
            export_obj._export_boe_file(cr, uid, ids, report)
        else:
            raise osv.except_osv( "ERROR", _('To export to BOE you need that the start period and end period was the same'))

        return True
        
    def _name_get(self, cr, uid, ids, field_name, arg, context={}):
        """
        Returns the report name
        """
        result = {}
        for report in self.browse(cr, uid, ids, context):
            result[report.id] = report.number
        return result
    
    def _get_number_records( self, cr, uid,ids, field_name, args,context ):
        
        result = {} 
        for id in ids:
            result[id] = {}.fromkeys(['number_records','total_taxable','total_sharetax','total'], 0.0)
    
        for model in self.browse(cr, uid, ids,context):

            for issue in model.issued:
                    result[model.id]['number_records'] += len( issue.tax_line_ids )
                    result[model.id]['total_taxable'] +=issue.base_tax
                    result[model.id]['total_sharetax'] +=issue.amount_tax
                    result[model.id]['total'] +=issue.base_tax + issue.amount_tax

            for issue in model.received:
                    result[model.id]['number_records'] += len( issue.tax_line_ids )
                    result[model.id]['total_taxable'] +=issue.base_tax
                    result[model.id]['total_sharetax'] +=issue.amount_tax
                    result[model.id]['total'] +=issue.base_tax + issue.amount_tax

        return result
            
    def on_change_name_contact(self, cr, uid, ids, name_contact):
        return  { 'value': { 'presenter_name': name_contact,'presenter_name_contact': name_contact } }
    
    def on_change_phone_contact(self, cr, uid, ids, phone_contact):
        return  { 'value': { 'presenter_phone_contact': phone_contact } }
    
    def on_change_representative_vat(self, cr, uid, ids, representative_vat):
        return  { 'value': { 'presenter_vat': representative_vat } }

    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.aeat.mod340'
    _description = 'Model 340'
    _columns = {
        'name': fields.function(_name_get, method=True, type="char", size="64", string="Name"),
        'contact_phone': fields.char("Phone", size=9),
        'phone_contact' : fields.char('Phone Contact',size=9),
        'name_contact' : fields.char('Name And Surname Contact',size=40),
        'period_from': fields.many2one('account.period', 'Start period',states={'done': [('readonly', True)]}),
        'period_to': fields.many2one('account.period', 'End period',states={'done': [('readonly', True)]}),
        'issued': fields.one2many('l10n.es.aeat.mod340.issued','mod340_id','Invoices Issued'),
        'received': fields.one2many('l10n.es.aeat.mod340.received','mod340_id','Invoices Received'),
        'investment': fields.one2many(
                                      'l10n.es.aeat.mod340.investment','mod340_id','Property Investment'),
        'intracomunitarias': fields.one2many('l10n.es.aeat.mod340.intracomunitarias','mod340_id','Operations Intracomunitarias'),
        
        'ean13': fields.char('Electronic Code VAT reverse charge', size=16),

        'total_taxable':  fields.function( _get_number_records, method=True, type='float',   string='Total Taxable',    multi='recalc', help="The declaration will include partners with the total of operations over this limit"),
        'total_sharetax': fields.function( _get_number_records, method=True, type='float',   string='Total Share Tax',  multi='recalc', help="The declaration will include partners with the total of operations over this limit"),
        'number_records': fields.function( _get_number_records, method=True, type='integer', string='Records',          multi='recalc', help="The declaration will include partners with the total of operations over this limit"),
        'total': fields.function( _get_number_records, method=True, type='float',   string="Total" ,           multi='recalc', help="The declaration will include partners with the total of operations over this limit"),
        'calculation_date': fields.date('Calculation date', readonly=True),
        # Data for type 0 register
        'presenter_vat': fields.char('VAT number', size=9,
            states={'confirmed':[('readonly',True)]}),
        'presenter_name' : fields.char('Name And Surname',size=40),
        'presenter_address_acronym' : fields.char('Address Acronym',size=2,
            help='Acronyms of the type of public roadway, example St.'),
        'presenter_address_name': fields.char('Street Name',size=52),
        'presenter_address_number': fields.integer('Number',size=5),
        'presenter_address_stair': fields.char('Stair', size=2),
        'presenter_address_floor': fields.char('Floor', size=2),
        'presenter_address_door': fields.char('Door', size=2),
        'presenter_city_id': fields.many2one('city.city', 'Location', select=1,
            help='Use the name or the zip to search the location'),
        'presenter_phone_contact' : fields.char('Phone Contact',size=9),
        'presenter_name_contact' : fields.char('Name And Surname Contact',size=40),
    }
    _defaults = {
        'support_type' : lambda *a: 'Telemático',
        'number' : lambda *a: '340',
        'type': lambda *a: 'Normal'
               }

    def set_done(self, cr, uid, id, *args):
        self.write(cr,uid,id,{'calculation_date': time.strftime('%Y-%m-%d'),'state': 'done',})
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340', id, 'done', cr)
        return True
    
    def _check_report_lines(self, cr, uid, ids, context=None):
        """checks report lines"""
#                if context is None: context = {}

#        for item in self.browse(cr, uid, ids, context):
#            ## Browse partner record lines to check if all are correct (all fields filled)
#            for partner_record in item.partner_record_ids:
#                if not partner_record.partner_state_code:
#                    raise osv.except_osv(_('Error!'), _("All partner state code field must be filled."))
#                if not partner_record.partner_vat:
#                    raise osv.except_osv(_('Error!'), _("All partner vat number field must be filled."))
#
#            for real_state_record in item.real_state_record_ids:
#                if not real_state_record.state_code:
#                    raise osv.except_osv(_('Error!'), _("All real state records state code field must be filled."))

        return True
    
    def check_report(self, cr, uid, ids, context=None):
        """Different check out in report"""
        if context is None: context = {}

        self._check_report_lines(cr, uid, ids, context)

        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        if context is None: context = {}

        self.check_report(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'done'})

        return True

    def confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""

        self.write(cr, uid, ids, {'state': 'done'})

        return True

    def cancel(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""

        self.write(cr, uid, ids, {'state': 'canceled'})

        return True
    
l10n_es_aeat_mod340()

class l10n_es_aeat_mod340_issued(osv.osv):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices invoice'
    _columns = {                        
        'mod340_id': fields.many2one('l10n.es.aeat.mod340','Model 340',ondelete="cascade"),
        'partner_id':fields.many2one('res.partner','Partner',ondelete="cascade"),
        'partner_vat':fields.char('Company CIF/NIF',size=12),
        'representative_vat': fields.char('L.R. VAT number', size=9, help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'invoice_id':fields.many2one('account.invoice','Invoice',ondelete="cascade"),
        'base_tax':fields.float('Base tax bill',digits=(13,2)),
        'amount_tax':fields.float('Total tax',digits=(13,2)),
        'total':fields.float('Total',digits=(13,2)),
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_issued', 'invoice_record_id', 'Tax lines', states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod340_issued()

class l10n_es_aeat_mod340_received(osv.osv):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'
    _columns = {
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_received', 'invoice_record_id', 'Tax lines', states = {'done': [('readonly', True)]}),
    }
l10n_es_aeat_mod340_received()

class l10n_es_aeat_mod340_investment(osv.osv):
    _name = 'l10n.es.aeat.mod340.investment'
    _description = 'Property Investment'
    _inherit = 'l10n.es.aeat.mod340.issued'
l10n_es_aeat_mod340_investment()

class l10n_es_aeat_mod340_intracomunitarias(osv.osv):
    _name = 'l10n.es.aeat.mod340.intracomunitarias'
    _description = 'Operations Intracomunitarias'
    _inherit = 'l10n.es.aeat.mod340.issued'
l10n_es_aeat_mod340_intracomunitarias()

class l10n_es_aeat_mod340_tax_line_issued(osv.osv):
    _name = 'l10n.es.aeat.mod340.tax_line_issued'
    _description = 'Mod340 vat lines issued'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),
        'tax_percentage': fields.float('Tax percentage',digits=(0,2)),
        'tax_amount': fields.float('Tax amount',digits=(13,2)),
        'base_amount': fields.float('Base tax bill',digits=(13,2)),
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.issued', 'Invoice issued', required=True, ondelete="cascade", select=1),
    }
l10n_es_aeat_mod340_tax_line_issued()

class l10n_es_aeat_mod340_tax_line_received(osv.osv):
    _name = 'l10n.es.aeat.mod340.tax_line_received'
    _description = 'Mod340 vat lines received'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.received', 'Invoice received', required=True, ondelete="cascade", select=1),
    }
l10n_es_aeat_mod340_tax_line_received()
