# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com) All Rights Reserved.
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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
from osv import fields,osv
import os
import pooler
import tools

class config_es_toponyms(osv.osv_memory):
    _name='config.es.toponyms'
    _inherit = 'res.config.installer'

    _columns = {
        'name':fields.char('Name', size=64),
        'state': fields.selection([('official','Official'),('spanish','Spanish'),('both','Both')], 'State names', required=True, help="Toponym version of the spanish states. For example: Official (Girona), Spanish (Gerona), Both (Gerona / Girona)"),
        'city_info': fields.selection([('yes','Yes'),('no','No')], 'City information', required=True, help="Do you want to add city and state information associated to the zip codes for all the spanish cities? This allows to fill automatically the city and states fields of partner and contact forms from the zip code."),
    }

    _defaults={
        'state': lambda *args: 'official',
        'city_info': lambda *args: 'yes',
    }
    
    def create_states(self, cr, uid, state_type, context=None):
		"""It imports spanish states information trough an XML file."""
		file_name = 'l10n_es_toponyms_states_%s.xml' %state_type
		try:
			fp = tools.file_open(os.path.join('l10n_es_toponyms', os.path.join('wizard', file_name)))
		except IOError, e:
			fp = None
		if fp:
			idref = {}
			tools.convert_xml_import(cr, 'l10n_es_toponyms', fp,  idref, 'init', noupdate=True)
			cr.commit()
			return True
		return False
	
    def create_zipcodes(self, cr, uid, context=None):
		"""It creates default values for state and city fields in res.partner model linked to zip codes (>15000 zip codes can take several minutes)."""
		from municipios_cpostal import cod_postales
		
		country_id = self.pool.get('res.country').search(cr, uid, [('code', '=', 'ES'),])[0]
		if country_id:
			ir_values_obj = self.pool.get('ir.values')
			for city in cod_postales:
				state_id = self.pool.get('res.country.state').search(cr, uid, [('country_id', '=', country_id), ('code', '=', city[0][:2]),])[0]
				if state_id:
					ir_values_obj.set(cr, uid, 'default', 'zip=' + city[0], 'state_id', [('res.partner', False)], state_id)
				ir_values_obj.set(cr, uid, 'default', 'zip=' + city[0], 'city', [('res.partner', False)], city[1])
			cr.commit()
		return {}

    def execute(self, cr, uid, ids, context=None):
		if context is None: context = {}
		super(config_es_toponyms, self).execute(cr, uid, ids, context=context)
		res = self.read(cr, uid, ids)[0]
		# Import spanish states (official, Spanish or both)
		self.create_states(cr, uid, res['state'], context=context)
		# Import spanish cities and zip codes
		if res['city_info'] == 'yes':
			self.create_zipcodes(cr, uid, context=context)

config_es_toponyms()
