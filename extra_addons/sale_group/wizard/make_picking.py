# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
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
import netsvc
import pooler


picking_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label colspan="4" string="Do you really want to create the pickings ?" />
    <field name="grouped" />
</form>'''


picking_fields = {
    'grouped' : {'string':'Group the pickings', 'type':'boolean', 'default': lambda *a: True}
}

wrong_state_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="One or more sale orders have are not confirmed" />
</form>'''

wrong_partner_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group sale orders from different partners" />
</form>'''
    
wrong_incoterm_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group sale orders with different incoterms" />
</form>'''

wrong_picking_policy_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group sale orders with different picking policies" />
</form>'''

wrong_shop_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group sale orders from different shops" />
</form>'''

def _checkState(self, cr, uid, data, context):
    order_obj = pooler.get_pool(cr.dbname).get('sale.order')
    orders = order_obj.browse(cr,uid,data['ids'])
    for order in orders:
        # Estados:
        # draft: Presupuesto (borrador)
        # progress : En Proceso (acceptados)
        # cancel: Cancelado
        if order.state <> 'progress':
            return 'wrong_state'
    return 'confirm'

def _checkValues(self, cr, uid, data, context):
    if data['form']['grouped']:
        order_obj = pooler.get_pool(cr.dbname).get('sale.order')
        orders = order_obj.browse(cr,uid,data['ids'])
        partner = orders[0].partner_id
        incoterm = orders[0].incoterm
        picking_policy = orders[0].picking_policy
        shop = orders[0].shop_id
        for order in orders:
            if partner != order.partner_id:
                return 'wrong_partner'
            if incoterm != order.incoterm:
                return 'wrong_incoterm'
            if picking_policy != order.picking_policy:
                return 'wrong_picking_policy'
            if shop != order.shop_id:
                return 'wrong_shop'
    return 'picking'

def _makePickings(self, cr, uid, data, context):
    order_obj = pooler.get_pool(cr.dbname).get('sale.order')
    newinv = []

    order_obj.action_ship_create(cr, uid, data['ids'], data['form']['grouped'])
    for id in data['ids']:
        wf_service = netsvc.LocalService("workflow")
        wf_service.trg_validate(uid, 'sale.order', id, 'manual_picking', cr)

    # Establece la relación entre pedidos y albaranes
    for o in order_obj.browse(cr, uid, data['ids'], context):
        for i in o.picking_ids:
            newinv.append(i.id)
    # Este return tipo ir.actions.act_window abre un nuevo formulario
    return {
        'domain': "[('id','in', ["+','.join(map(str,newinv))+"])]",
        'name': 'Pickings',
        'view_type': 'form',
        'view_mode': 'tree,form',
        'res_model': 'stock.picking',
        'view_id': False,
        #'context': "{'type':'out_refund'}",
        'type': 'ir.actions.act_window'
    }
    #return {}

class make_picking(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result': {'type':'choice', 'next_state':_checkState}
        },
        'confirm' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : picking_form,
                    'fields' : picking_fields,
                    'state' : [('end', 'Cancel'),('check_values', 'Create pickings') ]}
        },
        'wrong_state' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_state_form,
                    'fields' : {},
                    'state' : [('end', 'Acept')]}
        },
        'check_values' : {
            'actions' : [],
            'result' : {'type' : 'choice',
                    'next_state':_checkValues}
        },    
        'wrong_partner' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_partner_form,
                    'fields' : {},
                    'state' : [('end', 'Acept')]}
        },
        'wrong_incoterm' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_incoterm_form,
                    'fields' : {},
                    'state' : [('end', 'Acept')]}
        }, 
        'wrong_picking_policy' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_picking_policy_form,
                    'fields' : {},
                    'state' : [('end', 'Acept')]}
        }, 
        'wrong_shop' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_shop_form,
                    'fields' : {},
                    'state' : [('end', 'Acept')]}
        }, 
        'picking' : {
            'actions' : [],
            'result' : {'type' : 'action',
                    'action' : _makePickings,
                    'state' : 'end'}
        },
    }
make_picking("sale_group.make_picking")
