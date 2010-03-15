# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com) All Rights Reserved.
#                       Alejandro Sanchez <alejandro@asr-oss.com>
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

from osv import osv,fields
import time
import netsvc

class l10n_es_aeat_mod340_config(osv.osv):
    _name = 'l10n.es.aeat.mod340.config'
    _description = 'Config Model 340'
    _columns = {
        'name' : fields.char('Name',size=40),
        'taxes_id': fields.many2many('account.tax', 'mod340_config_taxes_rel','config_id', 'tax_id', 
            'Customer Taxes',domain=[('parent_id','=',False),('type_tax_use','in',['sale','all'])]),
        'supplier_taxes_id': fields.many2many('account.tax',
        'mod340_config_supplier_taxes_rel', 'config_id', 'tax_id',
            'Supplier Taxes', domain=[('parent_id', '=', False),('type_tax_use','in',['purchase','all'])])
    }
l10n_es_aeat_mod340_config()

class l10n_es_aeat_mod340(osv.osv):

    def _total_taxable(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for mod340 in self.browse(cursor, user, ids, context=context):
            res[mod340.id] = 0.0
            #registros emitidas
            if mod340.issued:
                res[mod340.id] = reduce(lambda x, y: x + y.taxable, mod340.issued, 0.0)
            #registros recibidas
            if mod340.received:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.taxable, mod340.received, 0.0)
            #registros investment
            if mod340.investment:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.taxable, mod340.investment, 0.0)
            #registros intracomunitarias
            if mod340.intracomunitarias:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.taxable, mod340.intracomunitarias, 0.0)

        return res

    def _total_share_tax(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for mod340 in self.browse(cursor, user, ids, context=context):
            res[mod340.id] = 0.0
            #registros emitidas
            if mod340.issued:
                res[mod340.id] = reduce(lambda x, y: x + y.share_tax, mod340.issued, 0.0)
            #registros recibidas
            if mod340.received:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.share_tax, mod340.received, 0.0)
            #registros investment
            if mod340.investment:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.share_tax, mod340.investment, 0.0)
            #registros intracomunitarias
            if mod340.intracomunitarias:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.share_tax, mod340.intracomunitarias, 0.0)

        return res

    def _total(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for mod340 in self.browse(cursor, user, ids, context=context):
            res[mod340.id] = 0.0
            #registros emitidas
            if mod340.issued:
                res[mod340.id] = reduce(lambda x, y: x + y.total, mod340.issued, 0.0)
            #registros recibidas
            if mod340.received:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.total, mod340.received, 0.0)
            #registros investment
            if mod340.investment:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.total, mod340.investment, 0.0)
            #registros intracomunitarias
            if mod340.intracomunitarias:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + y.total, mod340.intracomunitarias, 0.0)

        return res

    def _numer_records(self, cursor, user, ids, name, args, context=None):
        if not ids:
            return {}
        res = {}
        for mod340 in self.browse(cursor, user, ids, context=context):
            res[mod340.id] = 0.0
            #registros emitidas
            if mod340.issued:
                res[mod340.id] = reduce(lambda x, y: x + 1, mod340.issued, 0)
            #registros recibidas
            if mod340.received:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + 1, mod340.received, 0)
            #registros investment
            if mod340.investment:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + 1, mod340.investment, 0)
            #registros intracomunitarias
            if mod340.intracomunitarias:
                res[mod340.id] = res[mod340.id] + reduce(lambda x, y: x + 1, mod340.intracomunitarias, 0)

        return res
    _name = 'l10n.es.aeat.mod340'
    _description = 'Model 340'
    _columns = {
        'fiscalyear': fields.integer('Fiscal Year',size=4),
        'type': fields.selection([(' ','Normal'),('C','Complementary'),('S','Replacement')], 'Type Statement'),
        'type_support': fields.selection([('C','DVD'),('T','Telematics')],'Type Support'),
        'config_id': fields.many2one('l10n.es.aeat.mod340.config','Config',required=True),
        'company_id': fields.many2one('res.company', 'Company', required=True),
        'vat_representative' : fields.char('Vat Legal Representative',size=9),
        #'vat_company': fields.char('VAT', size=32, requiered=True),
        'name_surname': fields.char('Name and Surname',size=40),
        'phone': fields.char('Phone',size=9),
        'phone_contact' : fields.char('Phone Contact',size=9),
        'name_contact' : fields.char('Name And Surname Contact',size=40),
        'period': fields.selection([
            ('1T','First quarter'),('2T','Second quarter'),('3T','Third quarter'),
            ('4T','Fourth quarter'),('01','January'),('02','February'),('03','March'),('04','April'),
            ('05','May'),('06','June'),('07','July'),('08','August'),('09','September'),('10','October'),
            ('11','November'),('12','December')
            ], 'Period'),
        'issued': fields.one2many('l10n.es.aeat.mod340.issued','mod340_id','Invoices Issued'),
        'received': fields.one2many('l10n.es.aeat.mod340.received','mod340_id','Invoices Received'),
        'investment': fields.one2many('l10n.es.aeat.mod340.investment','mod340_id','Property Investment'),
        'intracomunitarias': fields.one2many('l10n.es.aeat.mod340.intracomunitarias','mod340_id','Operations Intracomunitarias'),
        'state': fields.selection([
            ('draft', 'Draft'),('open','Confirmed'),('cancel','Cancelled'),
            ('done','Done')
            ], 'State', select=True),
        'date_done': fields.date('Execution date', readonly=True),
        'number_records' : fields.function(_numer_records, string="Total Records", method=True,
            type='float'),
        'total_taxable': fields.function(_total_taxable, string="Total Taxable", method=True,
            type='float'),
        'total_sharetax': fields.function(_total_share_tax, string="Total Share Tax", method=True,
            type='float'),
        'total': fields.function(_total, string="Total", method=True,
            type='float'),
    }
    _defaults = {
        'fiscalyear': lambda *a: int(time.strftime('%Y')),
        'type': lambda *args: ' ',
        'type_support': lambda *args: 'T',
    }

    def set_done(self, cr, uid, id, *args):
        self.write(cr,uid,id,{'date_done': time.strftime('%Y-%m-%d'),'state': 'done',})
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340', id, 'done', cr)
        return True

    #def onchange_company_id(self, cr, uid, ids, company_id):
    #    vat = False
    #    if company_id:
    #        p = self.pool.get('res.company').browse(cr, uid, company_id)
    #        vat = p.partner_id.vat
    #        result = {'value':{'vat_company': vat}}
    #    return result

l10n_es_aeat_mod340()

class l10n_es_aeat_mod340_issued(osv.osv):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices Issued'
    _columns = {
        'mod340_id': fields.many2one('l10n.es.aeat.mod340','Model 340',ondelete="cascade"),
        'vat_declared' : fields.char('Vat Declared',size=9),
        'vat_representative' : fields.char('Legal Representative',size=9),
        'partner_name': fields.char('Name',size=40),
        'cod_country' : fields.char('Code Country',size=2),
        'key_country' : fields.selection([
            ('1','Nif'),('2','Nif/Iva'),('3','Passport'),('4','Dni'),('5','Fiscal Residence Certificate '),
            ('6','Other')
            ],'Key Ident Country'),
        'vat_country' : fields.char('Vat on Country of residence',size =17),
        'key_book' : fields.selection([
            ('E','Invoice Issued'),('I','Property Investment'),('R','Invoices Recibed'),
            ('U','Intra-Community Transactions'),('F','Invoice Issued IGIC'),
            ('J','Property Investment IGIC'),('S','Invoices Recibed IGIC')
            ],'Books'),
        'key_operation' : fields.selection([
            ('A','Account move Invoices'),('B','Account move Receipt'),
            ('C','Invoces varius tax rates'),('D','Amendment Invoices'),
            ('F','Travel Agency'),('G','IGIC'),('H','Gold Investment'),
            ('I','ISP'),('J','Receipt'),('K','Error correction'),
            ('L','None of the above')
            ],'Key Operation'),
        'invoice_date' : fields.date('Invoice Date'),
        'operation_date' : fields.date('Operation Date'),
        'rate' : fields.float('Rate',digits=(5,2)),
        'taxable' : fields.float('Taxable',digits=(13,2)),
        'share_tax' : fields.float('Share Tax',digits=(13,2)),
        'total' : fields.float('Total Invoice',digits=(13,2)),
        'taxable_cost' : fields.float('Taxable Cost',digits=(13,2)),
        'number' : fields.char('Invoice Number',size=40),
        'number_amendment' : fields.char('Number Invoice Amendment',size=40),
        #HASTA AQUI COMUNES EL RESTO ESPECIFICOS
        'number_invoices' : fields.integer('Invoices Accumulated',size = 4),
        'number_records' : fields.integer('Number records accumulated',size = 4),
        'iterval_ini' : fields.char('Initiation Interval',size=40),
        'iterval_end' : fields.char('Order Interval',size=40),
        'invoice_corrected' : fields.char('Invoice Corrected',size=40),
        'charge' : fields.float('Charge Equivalence',digits=(5,2)),
        'share_charge' : fields.float('Rate',digits=(5,2)),
    }
l10n_es_aeat_mod340_issued()

class l10n_es_aeat_mod340_received(osv.osv):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'
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
