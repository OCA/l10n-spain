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
import threading

class config_es_toponyms(osv.osv_memory):
    _name='config.es.toponyms'
    _inherit = 'res.config.installer'

    _columns = {
        'name':fields.char('Name', size=64),
        'state': fields.selection([('official','Official'),('spanish','Spanish'),('both','Both')], 'State names', required=True, help="Toponym version of the Spanish states. For example: Official (Girona), Spanish (Gerona), Both (Gerona / Girona)"),
        'city_info': fields.selection([('yes','Yes'),('no','No')], 'City information', required=True, help="Do you want to add city and state information associated to the zip codes for all the Spanish cities? This allows to fill automatically the city and states fields of partner and contact forms from the zip code."),
        'city_info_recover': fields.selection([('yes','Yes'),('no','No')], 'City information recover', required=True, help="Do you want to recover the location data (city information) from the zip code that was in the partner addresses before installing this module?"),
    }

    _defaults={
        'state': lambda *args: 'official',
        'city_info': lambda *args: 'yes',
        'city_info_recover': lambda *args: 'yes',
    }

    def onchange_city_info(self, cr, uid, ids, city_info):
        v = { 'city_info_recover': 'no' }
        if city_info == 'yes':
            v = { 'city_info_recover': 'yes' }
        return { 'value': v }

    def recover_zipcodes(self, cr, uid, context):
        """Recovers the location data (city info) from the zip code that is in the partner addresses."""
        address_obj = self.pool.get('res.partner.address')
        city_obj = self.pool.get('city.city')
        addresses_ids = address_obj.search(cr, uid, [('city_id','=', False)])
        addresses = address_obj.read(cr, uid, addresses_ids, ['zip'])
        cont = 0
        for address in addresses:
            if address['zip']:
                city_id = city_obj.search(cr, uid, [('zip', '=', address['zip'])])
                if len(city_id):
                    address_obj.write(cr, uid, address['id'], {'city_id' : city_id[0]})
                    cont += 1
        cr.commit()
        return cont
    
    def create_zipcodes(self, cr, uid, ids, res, context):
        """Imports Spanish cities and zip codes (can take several minutes)"""
        try:
            fp = tools.file_open(os.path.join('l10n_es_toponyms', 'l10n_es_toponyms_zipcodes.xml'))
        except IOError, e:
            fp = None
        if fp:
            idref = {}
            tools.convert_xml_import(cr, 'l10n_es_toponyms', fp,  idref, 'init', noupdate=True)
            cr.commit()
        return {}

    def execute(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        super(config_es_toponyms, self).execute(cr, uid, ids, context=context)
        res = self.read(cr, uid, ids)[0]

        # Import Spanish states (official, Spanish or both)
        file_name = 'l10n_es_toponyms_states_'+res['state']+'.xml'
        try:
            fp = tools.file_open(os.path.join('l10n_es_toponyms', file_name))
        except IOError, e:
            fp = None
        if fp:
            idref = {}
            tools.convert_xml_import(cr, 'l10n_es_toponyms', fp,  idref, 'init', noupdate=True)
            cr.commit()

        # Import Spanish cities and zip codes (in 6.1, it can be executed in the same thread)
        if res['city_info'] == 'yes':
            self.create_zipcodes(cr, uid, ids, res, context)

        # Recover city information
        if res['city_info_recover'] == 'yes':
            res= self.recover_zipcodes(cr, uid, context)

config_es_toponyms()
