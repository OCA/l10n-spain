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
import ir
import pooler

wrong_state_form = """<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <separator string="One or more sale order line is not confirmed" />
</form>"""

wrong_partner_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group lines from sale orders from different partners" />
</form>'''

wrong_incoterm_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group lines from sale orders with different incoterms" />
</form>'''

wrong_picking_policy_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group lines from sale orders with different picking policies" />
</form>'''

wrong_shop_form = '''<?xml version="1.0" encoding="utf-8"?>
<form string="Create pickings">
    <label string="It is not possible to group lines from sale orders with different shops" />
</form>'''

picking_form = """<?xml version="1.0" encoding="utf-8"?>
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

def _checkValues(self, cr, uid, data, context):
    if data['form']['grouped']:
        order_line_obj = pooler.get_pool(cr.dbname).get('sale.order.line')
        order_lines = order_line_obj.browse(cr,uid,data['ids'])
        partner = order_lines[0].order_id.partner_id
        incoterm = order_lines[0].order_id.incoterm
        picking_policy = order_lines[0].order_id.picking_policy
        shop = order_lines[0].order_id.shop_id
        for order_line in order_lines:
            if partner != order_line.order_id.partner_id:
                return 'wrong_partner'
            if incoterm != order_line.order_id.incoterm:
                return 'wrong_incoterm'
            if picking_policy != order_line.order_id.picking_policy:
                return 'wrong_picking_policy'
            if shop != order_line.order_id.shop_id:
                return 'wrong_shop'
    return 'picking'

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
                    ('check_values', 'Create pickings')
                ]
            }
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
