# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Factor Libre All Rights Reserved.
#    #    $Id$
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

from osv import osv
from osv import fields

class config_fiscal_position(osv.osv):
    _name = 'config.fiscal.position'
    _columns = {
        'name': fields.char('Config. Name', size=64),
        'fpos': fields.many2one('account.fiscal.position','Fiscal Position', required=True),
        'state_ids': fields.many2many('res.country.state', 'config_fpos_state_rel',
            'config_id', 'states_id', 'States'),
        'country_ids': fields.many2many('res.country', 'config_fpos_country_rel',
            'config_id', 'country_id', 'Countries'),
        'sequence': fields.integer('Sequence'),
        'vat_subjected': fields.boolean('VAT Legal Statement'),
        'vies_valid_vat': fields.boolean('Vies Valid Vat'),
    }
config_fiscal_position()
