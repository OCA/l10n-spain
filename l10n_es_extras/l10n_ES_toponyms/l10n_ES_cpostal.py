# -*- encoding: utf-8 -*-
##############################################################################
#
# Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#					Jordi Esteve <jesteve@zikzakmedia.com>
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

import ir
import wizard
import pooler
import codecs

cpostal_end_form = '''<?xml version="1.0"?>
<form string="Códigos postales">
	<separator string="Resultado:" colspan="4"/>
	<label string="Se han creado los municipios y provincias del Estado español asociados a códigos postales." colspan="4" align="0.0"/>
	<label string="Permite rellenar automáticamente los campos ciudad y provincia del formulario de empresa y contacto a partir del código postal." colspan="4" align="0.0"/>
</form>'''

class l10n_ES_crear_cpostal(wizard.interface):
	def _crear_cpostal(self, cr, uid, data, context):
		pool = pooler.get_pool(cr.dbname)
		idc = pool.get('res.country').search(cr, uid, [('code', '=', 'ES'),])
		if not idc:
			return
		idc = idc[0]
		con = codecs.open('./addons/l10n_ES_toponyms/municipios_cpostal.csv','r','utf-8')
		for linea in con:
			linea = linea[:-1]
			m = linea.split(";")
			ids = pool.get('res.country.state').search(cr, uid, [('country_id', '=', idc), ('code', '=', m[0][:2]),])
			if ids:
				ir.ir_set(cr, uid, 'default', 'zip='+m[0], 'state_id', [('res.partner.address', False)], ids[0])
			ir.ir_set(cr, uid, 'default', 'zip='+m[0], 'city', [('res.partner.address', False)], m[1])
		con.close()
		return {}

	states = {
		'init': {
			'actions': [_crear_cpostal],
			'result': {
				'type':'form',
				'arch':cpostal_end_form,
				'fields': {},
				'state':[('end', 'Aceptar', 'gtk-ok'),]
			}
		}
		
	}

l10n_ES_crear_cpostal('l10n_ES_toponyms.crear_cpostal')
