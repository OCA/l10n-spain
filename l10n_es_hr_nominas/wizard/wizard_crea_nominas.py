# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import wizard
import time
import datetime
import pooler

form = """<?xml version="1.0"?>
<form string="Generar Nominas">
    <field name="fecha"/>
    <field name="employee_ids" colspan="4" height="320" width="780"/>
</form>"""

fields = {
    'employee_ids': {'string': 'Empleados', 'type': 'many2many', 'relation': 'hr.employee', 'required': True},
    'fecha': {'string': 'Fecha Nómina', 'type': 'date', 'required': True, 'default': lambda *a: time.strftime('%Y-%m-' + str([31,28,31,30,31,30,31,31,30,31,30,31][time.localtime()[1]-1]))},

}

class crea_nominas(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.employee':
            data['form']['employee_ids'] = data['ids']
        return data['form']

    def _crea_nominas(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for emp_id in data['form']['employee_ids'][0][2]:
            empleado = pool.get('hr.employee').browse(cr, uid, emp_id)
            pool.get('hr.nomina').create(cr, uid, {'employee_id': empleado.id, 'fecha_nomina': data['form']['fecha'], 'retribucion_bruta': empleado.retribucion_bruta, 'ss_empresa': empleado.ss_empresa, 'ss_trabajador': empleado.ss_trabajador, 'irpf': empleado.irpf})

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancelar','gtk-no'),('crear_nominas','Crear Nóminas','gtk-yes')]}
        },
        'crear_nominas': {
            'actions': [],
            'result': {'type':'action', 'action':_crea_nominas, 'state':'end'}
        }
    }
crea_nominas('wiz_crear_nominas')


class crea_extras(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.employee':
            data['form']['employee_ids'] = data['ids']
        return data['form']

    def _crea_extras(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for emp_id in data['form']['employee_ids'][0][2]:
            empleado = pool.get('hr.employee').browse(cr, uid, emp_id)
            pool.get('hr.nomina').create(cr, uid, {'name': empleado.name + ' ' + str(data['form']['fecha']),'employee_id': empleado.id, 'fecha_nomina': data['form']['fecha'], 'retribucion_bruta': empleado.retribucion_bruta_extra, 'ss_empresa': empleado.ss_empresa_extra, 'ss_trabajador': empleado.ss_trabajador_extra, 'irpf': empleado.irpf_extra, 'extra': True})

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form, 'fields':fields, 'state':[('end','Cancelar','gtk-no'),('crear_anticipos','Crear Pagas Extra','gtk-yes')]}
        },
        'crear_anticipos': {
            'actions': [],
            'result': {'type':'action', 'action':_crea_extras, 'state':'end'}
        }
    }
crea_extras('wiz_crear_extras')


form_anticipos = """<?xml version="1.0"?>
<form string="Generar Anticipo">
    <field name="fecha"/>
    <field name="employee_ids" colspan="4" height="320" width="800"/>
    <field name="cantidad"/>
</form>"""

fields_anticipos = {
    'employee_ids': {'string': 'Empleados', 'type': 'many2many', 'relation': 'hr.employee', 'required': True},
    'fecha': {'string': 'Fecha Anticipo', 'type': 'date', 'required': True, 'default': lambda *a: time.strftime('%Y-%m-%d')},
    'cantidad': {'string': 'Cantidad Anticipo', 'type': 'float', 'required': True}
}

class crea_anticipos(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.employee':
            data['form']['employee_ids'] = data['ids']
        return data['form']

    def _crea_anticipos(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for emp_id in data['form']['employee_ids'][0][2]:
            empleado = pool.get('hr.employee').browse(cr, uid, emp_id)
            pool.get('hr.anticipo').create(cr, uid, {'employee_id': empleado.id, 'fecha_anticipo': data['form']['fecha'], 'cantidad': data['form']['cantidad']})

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form_anticipos, 'fields':fields_anticipos, 'state':[('end','Cancelar','gtk-no'),('crear_anticipos','Crear Anticipos','gtk-yes')]}
        },
        'crear_anticipos': {
            'actions': [],
            'result': {'type':'action', 'action':_crea_anticipos, 'state':'end'}
        }
    }
crea_anticipos('wiz_crear_anticipos')

