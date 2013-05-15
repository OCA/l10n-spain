# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2013 Servicios Baeza (http://www.serviciosbaeza.com/) All Rights Reserved.
#                       Pedro Manuel Baeza <pedro.baeza@gmail.com>
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com) All Rights Reserved.
#                       Ignacio Ibeas <ignacio@acysos.com>
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

from osv import osv, fields
import wizard
import pooler

class res_partner_address(osv.osv):
    _inherit = "res.partner.address"
    
    def on_change_city(self,cr,uid,ids,location):
        result = {}
        if location:
            city = self.pool.get('city.city').browse(cr, uid, location)
            result = {'value': {
                        'zip': city.zip,
                        'country_id': city.country_id.id,
                        'city': city.name,
                        'state_id': city.state_id.id
                    }
                }
        return result
    
    _columns = {
        'city_id': fields.many2one('city.city', 'Location', select=1,
        help='Use the name or the zip to search the location'),
    }
res_partner_address()
