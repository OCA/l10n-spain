# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
import logging

logger = logging.getLogger('city')

def migrate(cr, v):
    """
    Dump location info on address fields that are now empty after been 
    converted from function fields to normal ones.
    """
    logger.info('filling zip, city, state_id and country_id from city info')
    cr.execute("""UPDATE
                      res_partner_address as addr
                  SET
                      zip=city.zip,
                      city=city.name,
                      state_id=city.state_id,
                      country_id=city.country_id
                  FROM
                      city_city as city
                  WHERE
                      addr.city_id IS NOT NULL
                  AND
                      addr.city_id = city.id
                  """)
    logger.info('city info dump completed.')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
