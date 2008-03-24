#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# Copyright (c) 2005-2006 TINY SPRL. (http://tiny.be) All Rights Reserved.
#
# $Id: make_picking.py 1070 2005-07-29 12:41:24Z nicoe $
#
# WARNING: This program as such is intended to be used by professional
# programmers who take the whole responsability of assessing all potential
# consequences resulting from its eventual inadequacies and bugs
# End users who are looking for a ready-to-use solution with commercial
# garantees and support are strongly adviced to contract a Free Software
# Service Company
#
# This program is Free Software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
#
##############################################################################

import wizard
import netsvc
import pooler

picking_form = """<?xml version="1.0"?>
<form string="Create pickings">
    <separator colspan="4" string="Do you really want to create the pickings ?" />
    <field name="grouped" />
</form>
"""

picking_fields = {
    #'grouped' : {'string':'Group the pickings', 'type':'boolean', 'default': lambda x,y,z: True}
	'grouped' : {'string':'Group the pickings', 'type':'boolean', 'default': lambda *a: True}
}

wrong_state_form = """<?xml version="1.0"?>
<form string="Create pickings">
    <separator string="One or more sale orders have are not confirmed" />
</form>"""

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
        for orderline in order.order_line:
            print orderline.state
    return 'confirm'

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
                    'state' : [('end', 'Cancel'),('picking', 'Create pickings') ]}
        },
        'wrong_state' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_state_form,
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
