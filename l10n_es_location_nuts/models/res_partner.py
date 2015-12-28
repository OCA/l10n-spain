# -*- coding: utf-8 -*-
# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# © 2015 Antiun Ingenieria S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import models, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def onchange_state(self, state_id):
        result = super(ResPartner, self).onchange_state(state_id)
        state = self.env['res.country.state'].browse(state_id)

        # Ignore non-Spanish states
        if state.country_id.code == 'ES':
            nuts_state = self.env['res.partner.nuts'].search(
                [('level', '=', 4),
                 ('state_id', '=', state.id)],
                limit=1)

            # Update substate and region
            if nuts_state:
                substate = nuts_state.parent_id
                if substate:
                    result.setdefault("value", dict())
                    result["value"]["substate_id"] = substate.id
                    result["value"]["region_id"] = substate.parent_id.id

        return result
