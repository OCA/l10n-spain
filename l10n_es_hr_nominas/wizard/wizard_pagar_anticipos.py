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

form_pagar = """<?xml version="1.0"?>
<form string="Pagar Anticipos">
   <field name="anticipos_ids" height="320" width="780" domain="[('state','=','confirmado')]"/>
</form>"""

form_confirmar = """<?xml version="1.0"?>
<form string="Confirmar Anticipos">
   <field name="anticipos_ids" height="320" width="780" domain="[('state','=','borrador')]"/>
</form>"""

fields = {
    'anticipos_ids': {'string': 'Anticipos', 'type': 'many2many', 'relation': 'hr.anticipo', 'required': True},
}

class wizard_pagar_anticipo(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.anticipo':
            data['form']['anticipos_ids'] = data['ids']
        return data['form']

    def _pagar_anticipos(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for ant_id in data['form']['anticipos_ids'][0][2]:
            anticipo = pool.get('hr.anticipo').browse(cr, uid, ant_id)
            anticipo.pagar_anticipo(self, cr, uid, ant_id)

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form_pagar, 'fields':fields, 'state':[('end','Cancelar','gtk-no'),('pagar_anticipos','Pagar','gtk-yes')]}
        },
        'pagar_anticipos': {
            'actions': [],
            'result': {'type':'action', 'action':_pagar_anticipos, 'state':'end'}
        }
    }
wizard_pagar_anticipo('wizard_pagar_anticipos')


class wizard_confirmar_anticipo(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.anticipo':
            data['form']['anticipos_ids'] = data['ids']
        return data['form']

    def _confirmar_anticipos(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for ant_id in data['form']['anticipos_ids'][0][2]:
            anticipo = pool.get('hr.anticipo').browse(cr, uid, ant_id)
            anticipo.confirmar_anticipo(self, cr, uid, ant_id)

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form_confirmar, 'fields':fields, 'state':[('end','Cancelar','gtk-no'),('confirmar_anticipos','confirmar','gtk-yes')]}
        },
        'confirmar_anticipos': {
            'actions': [],
            'result': {'type':'action', 'action':_confirmar_anticipos, 'state':'end'}
        }
    }
wizard_confirmar_anticipo('wizard_confirmar_anticipos')
