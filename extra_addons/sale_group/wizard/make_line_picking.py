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
import ir
import pooler

wrong_state_form = """<?xml version="1.0"?>
<form string="Create pickings">
    <separator string="One or more sale order line is not confirmed" />
</form>"""

picking_form = """<?xml version="1.0"?>
<form string="Create pickings">
    <separator colspan="4" string="Do you really want to create the pickings ?" />
    <field name="grouped" />
</form>
"""

picking_fields = {
    'grouped' : {'string':'Group the pickings', 'type':'boolean', 'default': lambda *a: True}
}

def _checkState(self, cr, uid, data, context):
    order_line_obj = pooler.get_pool(cr.dbname).get('sale.order.line')   
    order_lines = order_line_obj.browse(cr,uid,data['ids'])
    for order_line in order_lines:
        print order_line.state
        if order_line.state <> 'confirmed':
            return 'wrong_state'           
    return 'confirm'

def _makePickings(self, cr, uid, data, context):
    order_line_obj = pooler.get_pool(cr.dbname).get('sale.order.line')  
    #pool = pooler.get_pool(cr.dbname)
    lines_ids = {}
    for line in order_line_obj.browse(cr,uid,data['ids']):
        if line.state == 'confirmed':
            """
            if not line.order_id.id in lines_ids:
                lines_ids[line.order_id.id] = [line.id]
            else:
                lines_ids[line.order_id.id].append(line.id)
            """                
            lines_ids.setdefault(line.order_id.id,[]).append(line.id)
    #pool.get('sale.order').action_ship_create(cr, uid, lines_ids.keys(), data['form']['grouped'], lines_ids = lines_ids)
    order_obj = pooler.get_pool(cr.dbname).get('sale.order')   
    order_obj.action_ship_create(cr, uid, lines_ids.keys(), data['form']['grouped'], lines_ids = lines_ids)
    """
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
    """
    return {}


class line_make_picking(wizard.interface):
    states = {
        'init' : {
            'actions' : [],
            'result': {'type':'choice', 'next_state':_checkState}
        },
        'confirm' : {
            'actions': [],
            'result': {
                'type': 'form',
                'arch': picking_form,
                'fields': picking_fields,
                'state': [
                    ('end', 'Cancel'),
                    ('picking', 'Create pickings')
                ]
            }
        },
        'picking' : {
            'actions' : [_makePickings],
            'result' : {'type': 'state', 'state': 'end'}
        },
        'wrong_state' : {
            'actions' : [],
            'result' : {'type' : 'form',
                    'arch' : wrong_state_form,
                    'fields' : {},
                    'state' : [('end', 'Acept')]}
        },
    }

line_make_picking("sale_group.make_line_picking")
