# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
#    Copyright (c) 2011-2013 Acysos S.L.(http://acysos.com) All Rights Reserved
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
#    Copyright (c) 2011 NaN Projectes de Programari Lliure, S.L.
#                       http://www.NaN-tic.com
#                   
#    $Id$
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

from openerp.osv import orm, fields
import time
import netsvc
import tools
import pooler


class l10n_es_aeat_mod340_report(orm.Model):
   
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
        
    def _name_get(self, cr, uid, ids, field_name, arg, context={}):
        """
        Returns the report name
        """
        result = {}
        for report in self.browse(cr, uid, ids, context):
            result[report.id] = report.number
        return result
    
    def _get_number_records( self, cr, uid,ids, field_name, args,context ):
        result = dict.fromkeys(ids, 
                               dict.fromkeys(['number_records','total_taxable','total_sharetax','total'], 0))
    
        for model in self.browse(cr, uid, ids,context):

            for invoice_rec in model.issued:
                result[model.id]['number_records'] += len( invoice_rec.tax_line_ids )
                result[model.id]['total_taxable'] += invoice_rec.base_tax
                result[model.id]['total_sharetax'] += invoice_rec.amount_tax
                result[model.id]['total'] += invoice_rec.base_tax + invoice_rec.amount_tax

            for invoice_rec in model.received:
                result[model.id]['number_records'] += len( invoice_rec.tax_line_ids )
                result[model.id]['total_taxable'] += invoice_rec.base_tax
                result[model.id]['total_sharetax'] += invoice_rec.amount_tax
                result[model.id]['total'] += invoice_rec.base_tax + invoice_rec.amount_tax
                
            for invoice_rec in model.investment:
                result[model.id]['number_records'] += len( invoice_rec.tax_line_ids )
                result[model.id]['total_taxable'] += invoice_rec.base_tax
                result[model.id]['total_sharetax'] += invoice_rec.amount_tax
                result[model.id]['total'] += invoice_rec.base_tax + invoice_rec.amount_tax
                
            for invoice_rec in model.intracomunitarias:
                result[model.id]['number_records'] += len( invoice_rec.tax_line_ids )
                result[model.id]['total_taxable'] += invoice_rec.base_tax
                result[model.id]['total_sharetax'] += invoice_rec.amount_tax
                result[model.id]['total'] += invoice_rec.base_tax + invoice_rec.amount_tax

        return result

    _inherit = "l10n.es.aeat.report"
    _name = 'l10n.es.aeat.mod340.report'
    _description = 'Model 340'
    _columns = {
        'name': fields.function(_name_get, method=True, type="char", 
                                size=64, string="Name"),
        'declaration_number': fields.char("Declaration number", size=64,
                                          readonly=True),
        'phone_contact': fields.char('Phone Contact',size=9),
        'name_contact': fields.char('Name And Surname Contact',size=40),
        'period_from': fields.many2one('account.period', 'Start period',
                                       states={'done': [('readonly', True)]}),
        'period_to': fields.many2one('account.period', 'End period',
                                     states={'done': [('readonly', True)]}),
        'issued': fields.one2many('l10n.es.aeat.mod340.issued','mod340_id',
                                  'Invoices Issued',
                                  states={'done': [('readonly', True)]}),
        'received': fields.one2many('l10n.es.aeat.mod340.received',
                                    'mod340_id','Invoices Received',
                                    states={'done': [('readonly', True)]}),
        'investment': fields.one2many('l10n.es.aeat.mod340.investment',
                                      'mod340_id','Investment Goods'),
        'intracomunitarias': fields.one2many(
                             'l10n.es.aeat.mod340.intracomunitarias',
                             'mod340_id','Intra-community Operations'),
        
        'ean13': fields.char('Electronic Code VAT reverse charge', size=16),

        'total_taxable': fields.function(_get_number_records, method=True,
            type='float', string='Total Taxable', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'total_sharetax': fields.function(_get_number_records, method=True,
            type='float', string='Total Share Tax', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'number_records': fields.function(_get_number_records, method=True,
            type='integer', string='Records', multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'total': fields.function(_get_number_records, method=True,
            type='float', string="Total", multi='recalc',
            help="""The declaration will include partners with the total 
                of operations over this limit"""),
        'investment_goods_prorating': fields.boolean("Investment goods prorating", 
            help="If checked, the investment goods invoices will be exported in their ledger. If not, they will be exported as received invoices")
    }
    _defaults = {
        'number': '340',
        'declaration_number': '340',
    }

    def set_done(self, cr, uid, id, *args):
        self.write(cr,uid,id,{'calculation_date': time.strftime('%Y-%m-%d'),
                              'state': 'done',})
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'l10n.es.aeat.mod340.report', 
                                id, 'done', cr)
        return True

    def action_confirm(self, cr, uid, ids, context=None):
        """set to done the report and check its records"""
        if context is None: context = {}

        self.check_report(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state': 'done'})

        return True

class l10n_es_aeat_mod340_issued(orm.Model):
    _name = 'l10n.es.aeat.mod340.issued'
    _description = 'Invoices invoice'
    
    def get_ledger_keys(self, cr, uid, context=None):
        return [('E', u'E-Libro registro de facturas expedidas.'),
                ('F', u'F-Libro registro de facturas expedidas IGIC.'),
                ('U', u'U-Libro registro de determinadas operaciones intracomunitarias (envío).')]

    def _get_ledger_keys(self, cr, uid, context=None):
        return self.get_ledger_keys(cr, uid, context=context)
    
    def get_operation_keys(self, cr, uid, context=None):
        return [(' ', u'Operación habitual'),
                ('A', u'A-Asiento resumen de facturas'),
                ('B', u'B-Asiento resumen de tique'),
                ('C', u'C-Factura con varios asientos (varios tipos impositivos)'),
                ('D', u'D-Factura rectificativa'),
                ('E', u'E-IVA/IGIC devengado pendiente de emitir factura'),
                ('G', u'G-Régimen especial de grupo de entidades en IVA o IGIC'),
                ('H', u'H-Régimen especial de oro de inversión'),
                ('I', u'I-Inversión del Sujeto pasivo (ISP)'),
                ('J', u'J-Tiques'),
                ('K', u'K-Rectificación de errores registrales'),
                ('M', u'M-IVA/IGIC facturado pendiente de devengar (emitida factura)'),
                ('N', u'N-Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre y por cuenta ajena'),
                ('O', u'O-Factura emitida en sustitución de tiques facturados y declarados'),
                ('Q', u'Q-Operaciones a las que se aplique el Régimen especial de bienes usados, objetos de arte, antigüedades y objetos de colección'),
                ('R', u'R-Operación de arrendamiento de local de negocio'),
                ('S', u'S-Subvenciones, auxilios o ayudas satisfechas o recibidas, tanto por parte de Administraciones públicas como de entidades privadas'),
                ('T', u'T-Cobros por cuenta de terceros de honorarios profesionales o de derechos derivados de la propiedad intelectual, industrial, de autor u otros por cuenta de sus socios, asociados o colegiados efectuados por sociedades, asociaciones, colegios profesionales u otras entidades que, entre sus funciones, realicen las de cobro'),
                ('U', u'U-Operación de seguros'),
                ('V', u'V-Compras de Agencias viajes'),
                ('W', u'W-Operaciones sujetas al Impuesto sobre la Producción, los Servicios y la Importación en las Ciudades de Ceuta y Melilla'),
                ('X', u'X-Operaciones por las que los empresarios o profesionales que satisfagan compensaciones agrícolas, ganaderas y/o pesqueras hayan expedido el recibo correspondiente'),
                ('Z', u'Z-Régimen especial del criterio de caja'),
                ('1', u'1-IVA criterio de caja. Asiento resumen de facturas'),
                ('2', u'2-IVA criterio de caja. Factura con varios asientos (varios tipos impositivos)'),
                ('3', u'3-IVA criterio de caja. Factura rectificativa'),
                ('4', u'4-IVA criterio de caja. Adquisiciones realizadas por las agencias de viajes directamente en interés del viajero (Régimen especial de agencia de viajes)'),
                ('5', u'5-IVA criterio de caja. Factura simplificada'),
                ('6', u'6-IVA criterio de caja. Rectificación de errores registrales'),
                ('7', u'7-IVA criterio de caja. Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre y por cuenta ajena. (Disposición adicional 4.ª RD 1496/2003)'),
                ('8', u'8-IVA criterio de caja. Operación de arrendamiento de local de negocio.')]
    
    def _get_operation_keys(self, cr, uid, context=None):
        return self.get_operation_keys(cr, uid, context=context)
    
    _columns = {                        
        'mod340_id': fields.many2one('l10n.es.aeat.mod340.report','Model 340',
                                     ondelete="cascade"),
        'partner_id': fields.many2one('res.partner','Partner',
                                     ondelete="cascade"),
        'partner_vat': fields.char('Company CIF/NIF',size=12),
        'representative_vat': fields.char('L.R. VAT number', size=9,
                                      help="Legal Representative VAT number"),
        'partner_country_code': fields.char('Country Code', size=2),
        'invoice_id':fields.many2one('account.invoice','Invoice',
                                     ondelete="cascade"),
        'base_tax': fields.float('Base tax bill',digits=(13,2)),
        'amount_tax': fields.float('Total tax',digits=(13,2)),
        'total': fields.float('Total',digits=(13,2)),
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_issued',
                                        'invoice_record_id', 'Tax lines'),
        'date_invoice': fields.date('Date Invoice', readonly=True),
        'ledger_key': fields.selection(_get_ledger_keys, 'Ledger Key', required=True, readonly=True),
        'operation_key': fields.selection(_get_operation_keys, 'Operation Key', required=True, readonly=True),
    }
    
    _order = 'date_invoice asc, invoice_id asc'

class l10n_es_aeat_mod340_received(orm.Model):
    _name = 'l10n.es.aeat.mod340.received'
    _description = 'Invoices Received'
    _inherit = 'l10n.es.aeat.mod340.issued'
    
    def get_ledger_keys(self, cr, uid, context=None):
        return [('R', u'R-Libro registro de facturas recibidas.'),
                ('I', u'I-Libro registro de bienes de inversión.'),
                ('J', u'J-Libro de registro de bienes de inversión IGIC.'),
                ('S', u'S-Libro de registro de facturas recibidas IGIC.'),
                ('U', u'U-Libro registro de determinadas operaciones intracomunitarias (recepción).')]

    def _get_ledger_keys(self, cr, uid, context=None):
        return self.get_ledger_keys(cr, uid, context=context)
    
    def get_operation_keys(self, cr, uid, context=None):
        return  [(' ', u'Operación habitual'),
                 ('A', u'A-Asiento resumen de facturas'),
                 ('B', u'B-Asiento resumen de tiques / facturas simplificadas'),
                 ('C', u'C-Factura con varios asientos(varios tipo impositivos)'),
                 ('D', u'D-Factura rectificativa'),
                 ('F', u'F-Adquisiciones realizadas por las agencias de viajes directamente en interés del viajero (Régimen especial de agencias de viajes)'),
                 ('G', u'G-Régimen especial de grupo de entidades en IVA o IGIC'),
                 ('H', u'H-Régimen especial de oro de inversión'),
                 ('I', u'I-Inversión del Sujeto pasivo (ISP)'),
                 ('J', u'J-Tiques / facturas simplificadas'),
                 ('K', u'K-Rectificación anotaciones registrales'),
                 ('L', u'L-Adquisiciones a comerciantes minoristas del IGIC'),
                 ('P', u'P-Adquisiciones intracomunitarias de bienes.'),
                 ('Q', u'Q-Operaciones a las que se aplique el régimen especial de bienes usados, ...'),
                 ('R', u'R-Operación de arrendamiento de local de negocio.'),
                 ('S', u'S-Subvenciones, auxilios o ayudas satisfechas o recibidas, tanto por parte de Administraciones públicas como de entidades privadas.'),
                 ('W', u'W-Operaciones sujetas al Impuesto sobre la Producción, los Servicios y la Importación en las Ciudades de Ceuta y Melilla.'),
                 ('X', u'X-Operaciones por las que los empresarios o profesionales que satisfagan compensaciones agrícolas, ganaderas y/o pesqueras hayan expedido el recibo correspondiente.'),
                 ('Z', u'Z-Régimen especial del criterio de caja.'),
                 ('1', u'1-IVA criterio de caja. Asiento resumen de facturas.'),
                 ('2', u'2-IVA criterio de caja. Factura con varios asientos (varios tipos impositivos).'),
                 ('3', u'3-IVA criterio de caja. Factura rectificativa.'),
                 ('4', u'4-IVA criterio de caja. Adquisiciones realizadas por las agencias de viajes directamente en interés del viajero (Régimen especial de agencias de viajes.'),
                 ('5', u'5-IVA criterio de caja. Factura simplificada.'),
                 ('6', u'6-IVA criterio de caja. Rectificación de errores registrales.'),
                 ('7', u'7-IVA criterio de caja. Facturación de las prestaciones de servicios de agencias de viaje que actúan como mediadoras en nombre y por cuenta ajena (Disposición adicional 4ª RD 1496/2003).'),
                 ('8', u'8-IVA criterio de caja. Operación de arrendamiento de local de negocio.')]
 
    def _get_operation_keys(self, cr, uid, context=None):
        return self.get_operation_keys(cr, uid, context=context)
    
    _columns = {
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_received',
                                       'invoice_record_id', 'Tax lines'),
        'ledger_key': fields.selection(_get_ledger_keys, 'Ledger Key', required=True, readonly=True),
        'operation_key': fields.selection(_get_operation_keys, 'Operation Key', required=True),
    }

class l10n_es_aeat_mod340_investment(orm.Model):
    _name = 'l10n.es.aeat.mod340.investment'
    _description = 'Property Investment'
    _inherit = 'l10n.es.aeat.mod340.received'
    
    _columns = {
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_investment',
                                        'invoice_record_id', 'Tax lines'),
        'use_date': fields.date("Goods use start date"),
        'prorata': fields.integer("Definitive yearly prorata"), 
    }
    
    _sql_constraints = [('prorata_range','check(prorata >= 0 and prorata <= 100)','The prorata must be between 0 and 100.')]

class l10n_es_aeat_mod340_intracomunitarias(orm.Model):
    _name = 'l10n.es.aeat.mod340.intracomunitarias'
    _description = 'Operations Intracomunitarias'
    _inherit = 'l10n.es.aeat.mod340.issued'
    
    _columns = {
        'tax_line_ids': fields.one2many('l10n.es.aeat.mod340.tax_line_intra',
                                        'invoice_record_id', 'Tax lines'),  
    }

class l10n_es_aeat_mod340_tax_line_issued(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_issued'
    _description = 'Mod340 vat lines issued'
    _columns = {
        'name': fields.char('Name', size=128, required=True, select=True),
        'tax_percentage': fields.float('Tax percentage',digits=(0,2)),
        'tax_amount': fields.float('Tax amount',digits=(13,2)),
        'base_amount': fields.float('Base tax bill',digits=(13,2)),
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.issued',
             'Invoice issued', required=True, ondelete="cascade", select=1),
        'surcharge_percentage': fields.float('Surcharge percentage',digits=(0,2)),
        'surcharge_amount': fields.float('Surcharge amount',digits=(13,2)),
    }

class l10n_es_aeat_mod340_tax_line_received(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_received'
    _description = 'Mod340 vat lines received'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.received',
             'Invoice received', required=True, ondelete="cascade", select=1),
    }
    
class l10n_es_aeat_mod340_tax_line_investment(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_investment'
    _description = 'Mod340 vat lines investment'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.investment',
             'Invoice received', required=True, ondelete="cascade", select=1),
        'goods_identification': fields.char("Investment goods identification", size=17),
    }

    

class l10n_es_aeat_mod340_tax_line_intra(orm.Model):
    _name = 'l10n.es.aeat.mod340.tax_line_intra'
    _description = 'Mod340 vat lines intra-community'
    _inherit = 'l10n.es.aeat.mod340.tax_line_issued'
    _columns = {
        'invoice_record_id': fields.many2one('l10n.es.aeat.mod340.intracomunitarias',
             'Invoice received', required=True, ondelete="cascade", select=1),
    }
