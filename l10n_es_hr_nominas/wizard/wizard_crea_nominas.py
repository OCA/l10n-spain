# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
#    Copyright (C) 2009 Ting! (<http://www.ting.es>). All Rights Reserved
#    Copyright (c) 2010 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Update to OpenERP 6.0 Ignacio Ibeas <ignacio@acysos.com> 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
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
from osv import osv, fields
from tools.translate import _
import wizard
import time
import datetime
import pooler
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class wizard_crea_nominas(osv.osv_memory):
    
    _name = 'wizard.crea.nominas'
    _description = 'Para crear nominas'
    
    _columns={
            #'employee_ids':{'string': 'Empleados', 'type': 'many2many', 'relation': 'hr.employee', 'required': True},
            'employee_ids':fields.many2many('hr.employee','rel_nominas_trabajadores','nomina_id','employee_id'),
            'fecha': fields.date('Fecha Nómina',required= True),
              }
    
    _defaults={
            'fecha': lambda *a: time.strftime('%Y-%m-' + str([31,28,31,30,31,30,31,31,30,31,30,31][time.localtime()[1]-1])),
               }

    def crea_nominas(self, cr, uid, ids, context):
        #########################################################################
        # OBJETOS
        #########################################################################
        nominas_obj = self.pool.get ('hr.employee')
        #########################################################################
        #pool = pooler.get_pool(cr.dbname)
        for wiz in self.browse(cr, uid, ids, context):
            data = wiz.fecha
            
        for emp_id in self.browse(cr, uid, ids[0], context).employee_ids:
            empleado = nominas_obj.browse(cr, uid, emp_id.id)
            val = {
                   'employee_id': empleado.id, 
                   'fecha_nomina':data, 
                   'retribucion_bruta': empleado.retribucion_bruta, 
                   'ss_empresa': empleado.ss_empresa, 
                   'ss_trabajador': empleado.ss_trabajador, 
                   'irpf': empleado.irpf,
                   }
            nomina = self.pool.get('hr.nomina').create(cr, uid, val)
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'}        
wizard_crea_nominas()


class wizard_crea_extras(osv.osv_memory):
    
    _name = 'wizard.crea.extras'
    _description = 'Para crear extras'
    
    _columns={
            #'employee_ids':{'string': 'Empleados', 'type': 'many2many', 'relation': 'hr.employee', 'required': True},
            'employee_ids':fields.many2many('hr.employee','rel_nominas_trabajadores','nomina_id','employee_id'),
            'fecha': fields.date('Fecha Nómina',required= True),
              }
    
    _defaults={
            'fecha': lambda *a: time.strftime('%Y-%m-' + str([31,28,31,30,31,30,31,31,30,31,30,31][time.localtime()[1]-1])),
               }

    def crea_extras(self, cr, uid, ids, context):
        #########################################################################
        # OBJETOS
        #########################################################################
        nominas_obj = self.pool.get ('hr.employee')
        #########################################################################
        #pool = pooler.get_pool(cr.dbname)
        for wiz in self.browse(cr, uid, ids, context):
            fecha = wiz.fecha
            
        for emp_id in self.browse(cr, uid, ids[0], context).employee_ids:
            empleado = nominas_obj.browse(cr, uid, emp_id.id)
            val ={
                  'employee_id': empleado.id,
                  'name': str(empleado.name) + ' ' + str((fecha)),
                  'fecha_nomina': fecha,
                  'retribucion_bruta': empleado.retribucion_bruta_extra,
                  'ss_empresa': empleado.ss_empresa_extra, 
                  'ss_trabajador': empleado.ss_trabajador_extra, 
                  'irpf': empleado.irpf_extra, 
                  'extra': True
                  }
            extras = self.pool.get('hr.nomina').create(cr, uid, val)
        return {'type': 'ir.actions.act_window_close'} 
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'}  
                                   
wizard_crea_extras()

class wizard_crea_anticipos(osv.osv_memory):
    
    _name = 'wizard.crea.anticipos'
    _description = ''
    
    _columns ={
            'employee_ids':fields.many2many('hr.employee','rel_nominas_trabajadores','nomina_id','employee_id'),
            'fecha': fields.date('Fecha Anticipo',required = True),
            'cantidad':fields.float('Cantidad Anticipo', required = True),
            }
    _defaults ={
            'fecha':  lambda *a: time.strftime('%Y-%m-%d'),
            }

    def crea_anticipos(self, cr, uid, ids, context):
        #########################################################################
        # OBJETOS
        #########################################################################
        nominas_obj = self.pool.get ('hr.employee')
        anticipos_obj = self.pool.get ('hr.anticipo')
        #########################################################################
        pool = pooler.get_pool(cr.dbname)
        for wiz in self.browse(cr, uid, ids, context):
            fecha = wiz.fecha
            cantidad = wiz.cantidad
       
        for emp_id in self.browse(cr, uid, ids[0], context).employee_ids:
            empleado = nominas_obj.browse(cr, uid, emp_id.id)
            val ={
                  'employee_id': empleado.id, 
                  'fecha_anticipo': fecha, 
                  'cantidad': cantidad,
                  }
            anticipos = anticipos_obj.create(cr, uid, val)
            
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'} 
     
wizard_crea_anticipos()
