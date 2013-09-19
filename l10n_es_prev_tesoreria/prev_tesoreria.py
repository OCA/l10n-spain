# -*- encoding: utf-8 -*-
##############################################################################
#
#    Avanzosc - Avanced Open Source Consulting
#    Copyright (C) 2010 - 2011 Avanzosc <http://www.avanzosc.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

import time
import decimal_precision as dp

from osv import osv
from osv import fields


class l10n_es_tesoreria_facturas(osv.osv):
    _name = 'l10n.es.tesoreria.facturas'
    _description = 'Facturas para la tesorería'
    _rec_name = 'factura_name'
    _columns = {
        'factura_id': fields.many2one('account.invoice', 'Factura'),
        'factura_name':fields.related('factura_id','number', type='char', size=32, string='Nombre Factura'),
        'fecha_vencimiento': fields.date('Fecha Vencimiento'),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'diario': fields.many2one('account.journal', 'Diario'),
        'tipo_pago': fields.many2one('payment.type', 'Tipo de Pago', required=False),
        'estado': fields.selection([
            ('draft','Borrador'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Abierto'),
            ('paid','Pagado'),
            ('cancel','Cancelado'),
        ], 'Estado'),
        'base': fields.float('Base', digits_compute=dp.get_precision('Account')),
        'impuesto': fields.float('Impuesto', digits_compute=dp.get_precision('Account')),
        'total': fields.float('Total', digits_compute=dp.get_precision('Account')),
        'pendiente': fields.float('Pendiente', digits_compute=dp.get_precision('Account')),
    }
l10n_es_tesoreria_facturas()

class l10n_es_tesoreria(osv.osv):
    _name = 'l10n.es.tesoreria'
    _description = 'Predicción de tesorería'
 
    def _check_fecha(self, cr, uid, ids): 
        for teso in self.browse(cr, uid, ids):
            if teso.inicio_validez > teso.fin_validez:
                return False
        return True
    
    def _check_filtro(self, cr, uid, ids):
        for teso in self.browse(cr, uid, ids):
            if not teso.check_draft and not teso.check_proforma and not teso.check_open:
                return False
        return True
    
    def _calcular_saldo(self, cr, uid, ids, name, args, context=None):
        res = {}
        saldo = 0
        for teso in self.browse(cr, uid, ids):
            for fact_emit in teso.facturas_emit:
                saldo += fact_emit.total
            for fact_rec in teso.facturas_rec:
                saldo -= fact_rec.total
            for pagoP in teso.pagos_period:
                saldo -= pagoP.importe
            for pagoV in teso.pagos_var:
                saldo -= pagoV.importe
            saldo += teso.saldo_inicial
            res[teso.id] = saldo
        return res
 
    _columns = {
        'name': fields.char('Descripción', size=64, required=True),
        'plantilla': fields.many2one('l10n.es.tesoreria.plantilla', 'Plantilla', required=True),
        'inicio_validez': fields.date('Fecha Inicio', required=True),
        'fin_validez': fields.date('Fecha Final', required=True),
        'saldo_inicial': fields.float('Saldo Inicial', digits_compute=dp.get_precision('Account')),
        'saldo_final': fields.function(_calcular_saldo, method=True, digits_compute=dp.get_precision('Account'), string='Saldo Final'),
        'check_draft': fields.boolean('Borrador'),
        'check_proforma': fields.boolean('Proforma'),
        'check_open': fields.boolean('Abierto'),
        'facturas_emit': fields.many2many('l10n.es.tesoreria.facturas', 'l10n_es_teso_fact_e_rel','teso_id','fact_e_id','Facturas Emitidas'),
        'facturas_rec': fields.many2many('l10n.es.tesoreria.facturas', 'l10n_es_teso_fact_r_rel','teso_id','fact_r_id','Facturas Recibidas'),
        'pagos_period': fields.one2many('l10n.es.tesoreria.pagos.period', 'tesoreria_id', 'Pagos Periodicos'),
        'pagos_var': fields.one2many('l10n.es.tesoreria.pagos.var', 'tesoreria_id', 'Pagos Variables'),
        'desglose_saldo': fields.one2many('l10n.es.tesoreria.saldos', 'tesoreria_id', 'Desglose de Saldo'),
    }
    
    _defaults = {  
        'check_draft': lambda *a: 1,
        'check_proforma': lambda *a: 1,
        'check_open': lambda *a: 1,
    }
    
    _constraints = [
            (_check_fecha, 'Error: Fecha final de validez', ['fin_validez']),
            (_check_filtro, 'Error: Selecciona un filtro', ['check_draft']),
    ]
    
    def restart(self, cr, uid, ids, context=None):
        pagoP_obj = self.pool.get('l10n.es.tesoreria.pagos.period')
        pagoV_obj = self.pool.get('l10n.es.tesoreria.pagos.var')
        t_factura_obj = self.pool.get('l10n.es.tesoreria.facturas')
        facturas = []
        for teso in self.browse(cr, uid, ids):
            for factura_emit in teso.facturas_emit:
                facturas.append(factura_emit.id)
            for factura_rec in teso.facturas_rec:
                facturas.append(factura_rec.id)
            t_factura_obj.unlink(cr, uid, facturas)
            for pagoP in teso.pagos_period:
                pagoP_obj.unlink(cr, uid, pagoP.id)
            for pagoV in teso.pagos_var:
                pagoV_obj.unlink(cr, uid, pagoV.id)
        return True
    
    def button_saldo(self, cr, uid, ids, context=None):
        res = {}
        saldo = 0
        saldos_obj = self.pool.get('l10n.es.tesoreria.saldos')
        for teso in self.browse(cr, uid, ids):
            for saldo in teso.desglose_saldo:
                saldos_obj.unlink(cr, uid, saldo.id)
            for fact_emit in teso.facturas_emit:
                saldo_id = saldos_obj.search(cr, uid, [('name','=',fact_emit.tipo_pago.name), ('tesoreria_id', '=', teso.id)])
                if saldo_id:
                    saldo = saldos_obj.browse(cr, uid, saldo_id[0])
                    saldos_obj.write(cr, uid, saldo.id, {'saldo': saldo.saldo + fact_emit.total})
                else:
                    saldos_obj.create(cr, uid, {'name': fact_emit.tipo_pago.name, 'saldo': fact_emit.total, 'tesoreria_id': teso.id})
            for fact_rec in teso.facturas_rec:
                saldo_id = saldos_obj.search(cr, uid, [('name','=',fact_rec.tipo_pago.name), ('tesoreria_id', '=', teso.id)])
                if saldo_id:
                    saldo = saldos_obj.browse(cr, uid, saldo_id[0])
                    saldos_obj.write(cr, uid, saldo.id, {'saldo': saldo.saldo - fact_rec.total})
                else:
                    saldos_obj.create(cr, uid, {'name': fact_rec.tipo_pago.name, 'saldo': -fact_rec.total, 'tesoreria_id': teso.id})
        return True
    
    def button_calculate(self, cr, uid, ids, context=None):
        facturas_emit = []
        facturas_rec = []
        estado = []
        pagoP_obj = self.pool.get('l10n.es.tesoreria.pagos.period')
        pagoV_obj = self.pool.get('l10n.es.tesoreria.pagos.var')
        t_factura_obj = self.pool.get('l10n.es.tesoreria.facturas')
        invoice_obj = self.pool.get('account.invoice')
        
        self.restart(cr, uid, ids)
        for teso in self.browse(cr, uid, ids):
            if teso.check_draft:
                estado.append("draft")
            if teso.check_proforma:
                estado.append("proforma")
            if teso.check_open:
                estado.append("open")
            invoices = invoice_obj.search(cr, uid, [('date_due', '>', teso.inicio_validez), ('date_due', '<', teso.fin_validez), ('state', 'in', tuple(estado))])
            for invoice in invoice_obj.browse(cr, uid, invoices):
                values = {
                    'factura_id': invoice.id,
                    'fecha_vencimiento': invoice.date_due,
                    'partner_id': invoice.partner_id.id,
                    'diario': invoice.journal_id.id,
                    'tipo_pago': invoice.payment_type.id,
                    'estado': invoice.state,
                    'base': invoice.amount_untaxed,
                    'impuesto': invoice.amount_tax,
                    'total': invoice.amount_total,
                    'pendiente': invoice.residual,
                }
                id = t_factura_obj.create(cr, uid, values)
                if invoice.type == "out_invoice":
                    facturas_emit.append(id)
                elif invoice.type == "in_invoice":
                    facturas_rec.append(id)
            self.write(cr, uid, teso.id, {'facturas_emit': [(6,0, facturas_emit)], 'facturas_rec': [(6,0, facturas_rec)]})
            for pagoP in teso.plantilla.pagos_period:
                if pagoP.fecha > teso.inicio_validez and pagoP.fecha < teso.fin_validez and not pagoP.pagado:
                    values = {
                        'name': pagoP.name,
                        'fecha': pagoP.fecha,
                        'partner_id': pagoP.partner_id.id,
                        'importe': pagoP.importe,
                        'tesoreria_id': teso.id,
                    }
                    pagoP_obj.create(cr, uid, values)
            for pagoV in teso.plantilla.pagos_var:
                if pagoV.fecha > teso.inicio_validez and pagoV.fecha < teso.fin_validez and not pagoV.pagado:
                    values = {
                        'name': pagoV.name,
                        'fecha': pagoV.fecha,
                        'partner_id': pagoV.partner_id.id,
                        'importe': pagoV.importe,
                        'tesoreria_id': teso.id,
                    }
                    pagoV_obj.create(cr, uid, values)
        return True
        
l10n_es_tesoreria()

class l10n_es_tesoreria_saldos(osv.osv):
    _name = 'l10n.es.tesoreria.saldos'
    _description = 'Saldos para la tesorería'
    
    _columns = {
        'name': fields.char('Tipo de Pago', size=64),
        'saldo': fields.float('Saldo', digits_compute=dp.get_precision('Account')),
        'tesoreria_id': fields.many2one('l10n.es.tesoreria', 'Tesoreria'),
    }
l10n_es_tesoreria_saldos()

class l10n_es_tesoreria_pagos_period(osv.osv):
    _name = 'l10n.es.tesoreria.pagos.period'
    _description = 'Pagos Periodicos para la tesorería'
    
    _columns = {
        'name': fields.char('Descripción', size=64),
        'fecha': fields.date('Fecha'),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'importe': fields.float('Importe', digits_compute=dp.get_precision('Account')),
        'tesoreria_id': fields.many2one('l10n.es.tesoreria', 'Tesorería'),
    } 
l10n_es_tesoreria_pagos_period()

class l10n_es_tesoreria_pagos_var(osv.osv):
    _name = 'l10n.es.tesoreria.pagos.var'
    _description = 'Pagos Variables para la tesorería'
    
    _columns = {
        'name': fields.char('Descripción', size=64),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'fecha': fields.date('Fecha'),
        'importe': fields.float('Importe', digits_compute=dp.get_precision('Account')),
        'tesoreria_id': fields.many2one('l10n.es.tesoreria', 'Tesorería'),
    } 
l10n_es_tesoreria_pagos_var()
