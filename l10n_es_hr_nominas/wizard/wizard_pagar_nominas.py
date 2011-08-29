# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>). All Rights Reserved
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
import wizard
import pooler

form_confirmar = """<?xml version="1.0"?>
<form string="Confirmar Nominas">
    <field name="nominas_ids" height="320" width="780" domain="[('state','=','borrador')]"/>
</form>"""

form_pagar = """<?xml version="1.0"?>
<form string="Pagar Nominas">
   <field name="nominas_ids" height="320" width="780" domain="[('state','=','confirmada')]"/>
</form>"""

fields = {
    'nominas_ids': {'string': 'Nominas', 'type': 'many2many', 'relation': 'hr.nomina', 'required': True},
}

class confirmar_nominas(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.nomina':
            data['form']['nominas_ids'] = data['ids']
        return data['form']

    def _confirma_nominas(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for nom_id in data['form']['nominas_ids'][0][2]:
            nom = pool.get('hr.nomina').browse(cr, uid, nom_id)
            nom.confirmar_nomina(self, cr, uid, nom_id)

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form_confirmar, 'fields':fields, 'state':[('end','Cancelar','gtk-no'),('confirmar_nominas','Confirmar','gtk-yes')]}
        },
        'confirmar_nominas': {
            'actions': [],
            'result': {'type':'action', 'action':_confirma_nominas, 'state':'end'}
        }
    }
confirmar_nominas('wizard_confirmar_nominas')


class pagar_nominas(wizard.interface):
    def _get_defaults(self, cr, uid, data, context={}):
        if data['model'] == 'hr.nomina':
            data['form']['nominas_ids'] = data['ids']
        return data['form']

    def _paga_nominas(self, cr, uid, data, context):
        pool = pooler.get_pool(cr.dbname)
        for nom_id in data['form']['nominas_ids'][0][2]:
            nom = pool.get('hr.nomina').browse(cr, uid, nom_id)
            nom.pagar_nomina(self, cr, uid, nom_id)

    states = {
        'init': {
            'actions': [_get_defaults],
            'result': {'type':'form', 'arch':form_pagar, 'fields':fields, 'state':[('end','Cancelar','gtk-no'),('pagar_nominas','Pagar','gtk-yes')]}
        },
        'pagar_nominas': {
            'actions': [],
            'result': {'type':'action', 'action':_paga_nominas, 'state':'end'}
        }
    }
pagar_nominas('wizard_pagar_nominas')
