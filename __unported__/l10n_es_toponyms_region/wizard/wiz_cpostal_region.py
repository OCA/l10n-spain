# -*- encoding: utf-8 -*-
##############################################################################
#
#    AvanzOSC, Avanzed Open Source Consulting 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
#    
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from osv import osv, fields
from openerp import pooler


class wizard_create_zipcode_region(osv.osv_memory):
    
    _name = 'wizard.create.zipcode.region'
    _description = 'crete zip code for regions'
    
    def ir_set(self,cr, uid, key, key2, name, models, value, replace=True, isobject=False, meta=None):
        obj = ir_values_obj = self.pool.get('ir.values')
        return obj.set(cr, uid, key, key2, name, models, value, replace, isobject, meta)

    def ir_del(self, cr, uid, id):
        obj = ir_values_obj = self.pool.get('ir.values')
        return obj.unlink(cr, uid, [id])

    def ir_get(self, cr, uid, key, key2, models, meta=False, context=None, res_id_req=False):
        obj = ir_values_obj = self.pool.get('ir.values')
        res = obj.get(cr, uid, key, key2, models, meta=meta, context=context, res_id_req=res_id_req)
        return res
     
    def create_zipcode(self, cr, uid, ids, context):
        #################################################################
        # OBJETOS
        #################################################################
        res_country_region_obj = self.pool.get('res.country.region')
        ir_values_obj = self.pool.get('ir.values')
        #################################################################
        com_auto={'00':'', '01':'EK', '02':'CM', '03':'PV', '04':'AN', '05':'CL', '06':'EX', '07':'IB', '08':'CA', '09':'CL', '10':'EX', '11':'AN', '12':'PV', '13':'CM', '14':'AN', '15':'GA', '16':'CM', '17':'CA', '18':'AN', '19':'CM', '20':'EK', '21':'AN', '22':'AR', '23':'AN', '24':'CL', '25':'CA', '26':'LR', '27':'GA', '28':'MA', '29':'AN', '30':'MU', '31':'NA', '32':'GA', '33':'AS', '34':'CL', '35':'IC', '36':'GA', '37':'CL', '38':'IC', '39':'CB', '40':'CL', '41':'AN', '42':'CL', '43':'CA', '44':'AR', '45':'CM', '46':'PV', '47':'CL', '48':'EK', '49':'CL', '50':'AR', '51':'CE', '52':'ME'}
        from cpostal import cod_postales
        pool = pooler.get_pool(cr.dbname)
        for m in cod_postales:
            codi = m[0][:-3] #2 primeros dígitos del cp
            county_ids = res_country_region_obj.search(cr, uid, [('code', '=', com_auto[codi])])
            if county_ids:
                #ir_values_obj.ir_set(cr, uid, 'default', 'zip='+m[0], 'region', [('res.partner.address', False)], county_ids[0])
                self.ir_set(cr, uid, 'default', 'zip='+m[0], 'region', [('res.partner.address', False)], county_ids[0])
        return {'type': 'ir.actions.act_window_close'}
    
    def cerrar(self, cr, uid, ids, context): 
        return {'type': 'ir.actions.act_window_close'} 

wizard_create_zipcode_region()