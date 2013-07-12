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
        'state': fields.selection([('official','Official'),('spanish','Spanish'),('both','Both')], 'State names', required=True),
        'city_info': fields.selection([('yes','Yes'),('no','No')], 'City information', required=True),
    }

    _defaults={
        'state': lambda *args: 'official',
        'city_info': lambda *args: 'yes',
    }
    
    def create_states(self, cr, uid, state_type, context=None):
		"""Import spanish states information through an XML file."""
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
        """Import spanish zipcodes information through an XML file."""
        file_name = 'l10n_es_toponyms_zipcodes.xml'
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
