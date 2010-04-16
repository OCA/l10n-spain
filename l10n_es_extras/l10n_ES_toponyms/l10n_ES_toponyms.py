# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

from osv import fields,osv
import os
import ir
import pooler
import tools
import threading

class config_ES_toponyms(osv.osv_memory):
    _name='config.ES.toponyms'

    def _city_module_default(self, cr, uid, context=None):
        cr.execute('select * from ir_module_module where name=%s and state=%s', ('city','installed'))
        if cr.fetchone():
            return 'installed'
        else:
            return 'uninstalled'

    def _city_info_recover_default(self, cr, uid, context=None):
        # City info can be selected if zip field exists in the database. That will happen only
        # if module city wasn't installed by the initial profile.
        cr.execute("select * from information_schema.columns where table_name='res_partner_address' and table_schema='public' and column_name='zip'")
        if cr.fetchone():
            return 'yes'
        else:
            return 'no'

    _columns = {
        'name':fields.char('Name', size=64),
        'state': fields.selection([('official','Official'),('spanish','Spanish'),('both','Both')], 'State names', required=True, help="Toponym version of the Spanish states. For example: Official (Girona), Spanish (Gerona), Both (Gerona / Girona)"),
        'city_module': fields.selection([('installed','Installed'),('uninstalled','Uninstalled')], 'City module', readonly=True, help="City module is optional and groups state, city and zip code in one entity."),
        'city_info': fields.selection([('yes','Yes'),('no','No')], 'City information', required=True, help="Do you want to add city and state information associated to the zip codes for all the Spanish cities? This allows to fill automatically the city and states fields of partner and contact forms from the zip code."),
        'city_info_recover': fields.selection([('yes','Yes'),('no','No')], 'City information recover', required=True, help="If the city module has been installed, do you want to recover the location data (city information) from the zip code there was in the partner addresses before installing the city module?"),
    }

    _defaults={
        'state': lambda *args: 'official',
        'city_module': _city_module_default,
        'city_info': lambda *args: 'yes',
        'city_info_recover': _city_info_recover_default,
    }

    def onchange_city_info(self, cr, uid, ids, city_info, city_module):
        if city_module == 'uninstalled':
            v = {'city_info_recover': 'no'}
        elif city_info == 'yes':
            v = {
                'city_info_recover': self._city_info_recover_default(cr, uid)
            }
        return {'value':v}

    def _onchange_city_info(self, cr, uid, ids, city_info, city_module):
        """onchange_city_info alias for backwards compatibility"""
        return self._onchange_city_info(cr, uid, ids, city_info, city_module)

    def _create_defaults(self, cr, uid, context):
        # Creates default values of state and city res.partner.address fields linked to zip codes
        from municipios_cpostal import cod_postales
        pool = pooler.get_pool(cr.dbname)
        idc = pool.get('res.country').search(cr, uid, [('code', '=', 'ES'),])
        if not idc:
            return
        idc = idc[0]
        for m in cod_postales:
            ids = pool.get('res.country.state').search(cr, uid, [('country_id', '=', idc), ('code', '=', m[0][:2]),])
            if ids:
                ir.ir_set(cr, uid, 'default', 'zip='+m[0], 'state_id', [('res.partner.address', False)], ids[0])
            ir.ir_set(cr, uid, 'default', 'zip='+m[0], 'city', [('res.partner.address', False)], m[1])
        return {}


    def _recover_zipcodes(self, cr, uid, context):
        # Recovers the location data (city info) from the zip code there was in the partner addresses before installing the city module
        cr.execute("select id, zip from res_partner_address where location IS NULL")
        zipcodes = cr.dictfetchall()
        cont = 0
        for zipcode in zipcodes:
            if zipcode['zip']:
                cr.execute("select id from city_city where zipcode = '%s'" %zipcode['zip'])
                city_id = cr.fetchall()
                if len(city_id) > 0:
                    cr.execute("update res_partner_address SET location = %i WHERE id = %i" %(city_id[0][0], zipcode['id']))
                    cont += 1
        return cont


    def create_zipcodes(self, db_name, uid, ids, res, context):
        # Import Spanish cities and zip codes (15000 zip codes can take several minutes)
        db, pool = pooler.get_db_and_pool(db_name)
        cr = db.cursor()
        if res['city_module'] == 'uninstalled': # city module no installed
            self._create_defaults(cr, uid, context)
        else:                                   # city module installed
            try:
                fp = tools.file_open(os.path.join('l10n_ES_toponyms', 'l10n_ES_toponyms_zipcodes.xml'))
            except IOError, e:
                fp = None
            if fp:
                idref = {}
                tools.convert_xml_import(cr, 'l10n_ES_toponyms', fp,  idref, 'init', noupdate=True)
                if res['city_info_recover'] == 'yes':
                    res= self._recover_zipcodes(cr, uid, context)
                    #print res
        cr.commit()
        cr.close()
        return {}


    def action_set(self, cr, uid, ids, context=None):
        res = self.read(cr, uid, ids)[0]
        #print res

        # Import Spanish states (official, Spanish or both)
        file_name = 'l10n_ES_toponyms_states_'+res['state']+'.xml'
        try:
            fp = tools.file_open(os.path.join('l10n_ES_toponyms', file_name))
        except IOError, e:
            fp = None
        if fp:
            idref = {}
            tools.convert_xml_import(cr, 'l10n_ES_toponyms', fp,  idref, 'init', noupdate=True)

        # Import Spanish cities and zip codes in other thread (15000 zip codes can take several minutes)
        if res['city_info'] == 'yes':
            cr.commit()
            thread1 = threading.Thread(target=self.create_zipcodes, args=(cr.dbname, uid, ids, res, context))
            thread1.start()

        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'ir.actions.configuration.wizard',
                'type': 'ir.actions.act_window',
                'target':'new',
            }


    def action_cancel(self, cr, uid, ids, conect=None):
        return {
                'view_type': 'form',
                "view_mode": 'form',
                'res_model': 'ir.actions.configuration.wizard',
                'type': 'ir.actions.act_window',
                'target':'new',
         }

config_ES_toponyms()
