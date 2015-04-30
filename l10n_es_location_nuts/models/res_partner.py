# -*- coding: utf-8 -*-
# Python source code encoding : https://www.python.org/dev/peps/pep-0263/
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2015 Antiun Ingenieria, SL (Madrid, Spain, http://www.antiun.com)
#                 Antonio Espinosa <antonioea@antiun.com>
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

from openerp import models, api
from openerp.addons.base_location_nuts.models.res_partner \
    import dict_recursive_update


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def onchange_state(self, state_id):
        result = super(ResPartner, self).onchange_state(state_id)
        state = self.env['res.country.state'].browse(state_id)
        if state.country_id.code == 'ES':
            region_id = False
            substate_id = False
            nuts_state = self.env['res.partner.nuts'].search(
                [('level', '=', 4),
                 ('state_id', '=', state.id)])
            if nuts_state:
                substate = nuts_state[0].parent_id
                if substate:
                    substate_id = substate.id
                    region_id = substate.parent_id.id
            changes = {
                'domain': {
                    'substate': [('country_id', '=', 'ES'),
                                 ('level', '=', 3)],
                    'region': [('country_id', '=', 'ES'),
                               ('level', '=', 2)],
                },
                'value': {
                    'substate': substate_id,
                    'region': region_id,
                }
            }
            dict_recursive_update(result, changes)
        return result

    @api.onchange('substate', 'region')
    def onchange_substate_or_region(self):
        result = super(ResPartner, self).onchange_substate_or_region()
        if (self.state_id.country_id.code == 'ES' or
                self.substate.country_id.code == 'ES' or
                self.region.country_id.code == 'ES'):
            changes = {
                'domain': {
                    'substate': [('country_id', '=', 'ES'),
                                 ('level', '=', 3)],
                    'region': [('country_id', '=', 'ES'),
                               ('level', '=', 2)],
                }
            }
            if self.substate.country_id.code == 'ES':
                self.region = self.substate.parent_id
                self.country_id = self.substate.country_id
            if self.region.country_id.code == 'ES':
                self.country_id = self.region.country_id
            if self.state_id.country_id.code == 'ES':
                self.country_id = self.state_id.country_id

            dict_recursive_update(result, changes)
        return result
