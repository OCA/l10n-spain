# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2007 ACYSOS S.L. - Pedro Tarrafeta (ptarra@gmail.com) 
#
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
import pooler
import time
from osv import osv
import tools
import base64
import StringIO
import csv


main_form = '''<?xml version="1.0"?>
<form string="Stock at:">
 <field name="fecha"/>
</form>
'''

main_fields = {
		'fecha': {
			'string': 'Date for stocks:',
			'type': 'date',
			'default': lambda *a: time.strftime('%Y-%m-%d'),
		},
}

finnish_form = '''<?xml version="1.0"?>
<form string="Stock calculated">
 <field name="stock_file" />
</form>
'''

finnish_fields = {
	'stock_file': {
		'string': 'CSV file',
		'type': 'binary',
		'readonly' : True,
	}
}
def _create_file(self, cr, uid, data, context):
	buf = StringIO.StringIO()

        def process(location_id):
		location_name = pooler.get_pool(cr.dbname).get('stock.location').read(cr,uid,[location_id], ['name'])  
                buf.write(location_name[0]['name'])
		buf.write("  -  " + data['form']['fecha'])
		buf.write('\n') 
                prod_info = pooler.get_pool(cr.dbname).get('stock.location')._product_get(cr, uid, location_id, date_ref=data['form']['fecha'])
                for prod_id in prod_info.keys():
                	if prod_info[prod_id] != 0.0:
                        	prod_name = pooler.get_pool(cr.dbname).get('product.product').read(cr, uid, [prod_id], ['name', 'categ_id', 'default_code', 'product_manager'])
				categ_name = prod_name[0]['categ_id'][1]
				buf.write(categ_name.replace(';','')  + ";")
				buf.write(prod_name[0]['name'].replace(';','')+ ";")
				codigo = prod_name[0]['default_code'] or " "
				buf.write(codigo.replace(';','') + ";")
				if prod_name[0]['product_manager']:
					buf.write(prod_name[0]['product_manager'][1].replace(';','') + ";")
				else:
					buf.write(" ;")
				buf.write(str(prod_info[prod_id]).replace('.',','))
				buf.write("\n")
                location_child = pooler.get_pool(cr.dbname).get('stock.location').read(cr, uid, [location_id], ['child_ids'])
                for child_id in location_child[0]['child_ids']:
			process(child_id)
                return buf

	for location_id in data['ids']:
                        buf.write(process(location_id) )

	out=base64.encodestring(buf.getvalue())
	buf.close()

	return {'stock_file': out}

class wizard_stock_content_location(wizard.interface):
	states = {
		'init': {
			'actions': [],
			'result': {'type': 'form', 'arch': main_form, 'fields': main_fields, 'state': [('end', 'Cancel', 'gtk-cancel'), ('calc', 'Ok', 'gtk-ok')]},
			},
		'calc': {
			'actions': [_create_file],
			'result': {'type':'form', 'arch': finnish_form, 'fields': finnish_fields, 'state': [('end', 'Close', 'gtk-cancel')]}
		}
	}

wizard_stock_content_location('stock.past.content.location')

