# -*- coding: utf-8 -*-
# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# © 2015 Antiun Ingenieria S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api
from openerp.tools.translate import _
from openerp.addons.base_location_nuts.models.res_partner \
    import dict_recursive_update


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    @api.depends('country_id')
    def _labels_get(self):
        super(ResPartner, self)._labels_get()
        if self.country_id.code == 'ES':
            self.lbl_substate = _('Autonomous Community')
            self.lbl_region = _('Region')

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
