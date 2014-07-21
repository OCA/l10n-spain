# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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
                                                                                             
from openerp import pooler
from osv import osv, fields

com_auto={'00':'', '01':'EK', '02':'CM', '03':'PV', '04':'AN', '05':'CL', '06':'EX', '07':'IB', '08':'CA', '09':'CL', '10':'EX', '11':'AN', '12':'PV', '13':'CM', '14':'AN', '15':'GA', '16':'CM', '17':'CA', '18':'AN', '19':'CM', '20':'EK', '21':'AN', '22':'AR', '23':'AN', '24':'CL', '25':'CA', '26':'LR', '27':'GA', '28':'MA', '29':'AN', '30':'MU', '31':'NA', '32':'GA', '33':'AS', '34':'CL', '35':'IC', '36':'GA', '37':'CL', '38':'IC', '39':'CB', '40':'CL', '41':'AN', '42':'CL', '43':'CA', '44':'AR', '45':'CM', '46':'PV', '47':'CL', '48':'EK', '49':'CL', '50':'AR', '51':'CE', '52':'ME'}

class region(osv.osv):
    _name = 'res.country.region'
    _description = 'Region'
    _columns = {
        'country_id': fields.many2one('res.country', 'Country', required=True),
        'name': fields.char('Name', size=64, required=True),
        'code': fields.char('Code', size=10),
            }
    _order = 'name'
region()

class res_partner_address(osv.osv):
    _name = 'res.partner.address'
    _inherit = 'res.partner.address'
    _columns = {
        'region': fields.many2one('res.country.region', 'Region', domain="[('country_id', '=', country_id)]"),
    }
res_partner_address()
