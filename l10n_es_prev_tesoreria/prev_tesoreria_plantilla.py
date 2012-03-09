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

class l10n_es_tesoreria_plantilla(osv.osv):
    _name = 'l10n.es.tesoreria.plantilla'
    _description = 'Plantilla Predicción de tesorería'
 
    _columns = {
        'name': fields.char('Descripción', size=64),
        'pagos_period': fields.one2many('l10n.es.tesoreria.pagos.period.plan', 'plan_tesoreria_id', 'Pagos Periodicos'),
        'pagos_var': fields.one2many('l10n.es.tesoreria.pagos.var.plan', 'plan_tesoreria_id', 'Pagos Variables'),
    }
        
l10n_es_tesoreria_plantilla()

class l10n_es_tesoreria_pagos_period_plan(osv.osv):
    _name = 'l10n.es.tesoreria.pagos.period.plan'
    _description = 'Plantilla Pagos Periodicos para la tesorería'
    
    _columns = {
        'name': fields.char('Descripción', size=64),
        'fecha': fields.date('Fecha'),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'diario': fields.many2one('account.journal', 'Diario', domain=[('type', '=', 'purchase')]),
        'factura_id': fields.many2one('account.invoice', 'Factura', domain=[('type', '=', 'in_invoice')]),
        'importe': fields.float('Importe', digits_compute=dp.get_precision('Account')),
        'pagado': fields.boolean('Facturado/Pagado'),
        'plan_tesoreria_id': fields.many2one('l10n.es.tesoreria.plantilla', 'Plantilla Tesorería'),
    } 
    
    def onchange_factura(self, cr, uid, ids, factura_id, context=None):
        values = {}
        invoice_obj = self.pool.get('account.invoice')
        if factura_id:
            invoice = invoice_obj.browse(cr, uid, factura_id)
            values = {
                'diario': invoice.journal_id.id
            }
        return {'value': values}
    
l10n_es_tesoreria_pagos_period_plan()

class l10n_es_tesoreria_pagos_var_plan(osv.osv):
    _name = 'l10n.es.tesoreria.pagos.var.plan'
    _description = 'Plantilla Pagos Variables para la tesorería'
    
    _columns = {
        'name': fields.char('Descripción', size=64),
        'partner_id': fields.many2one('res.partner', 'Empresa'),
        'fecha': fields.date('Fecha'),
        'diario': fields.many2one('account.journal', 'Diario', domain=[('type', '=', 'purchase')]),
        'factura_id': fields.many2one('account.invoice', 'Factura', domain=[('type', '=', 'in_invoice')]),
        'importe': fields.float('Importe', digits_compute=dp.get_precision('Account')),
        'pagado': fields.boolean('Pagado'),
        'plan_tesoreria_id': fields.many2one('l10n.es.tesoreria.plantilla', 'Plantilla Tesorería'),
    }
    
    def onchange_factura(self, cr, uid, ids, factura_id, context=None):
        values = {}
        invoice_obj = self.pool.get('account.invoice')
        if factura_id:
            invoice = invoice_obj.browse(cr, uid, factura_id)
            values = {
                'diario': invoice.journal_id.id
            }
        return {'value': values}
    
l10n_es_tesoreria_pagos_var_plan()