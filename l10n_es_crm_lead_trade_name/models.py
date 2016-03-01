# -*- coding: utf-8 -*-
# © 2015 Antiun Ingeniería, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class Lead(models.Model):
    _inherit = "crm.lead"

    trade_name = fields.Char()

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        """Add trade name to partner."""
        ctx = {"default_comercial": lead.trade_name}
        return (super(Lead, self.with_context(**ctx))
                ._lead_create_contact(lead, name, is_company, parent_id))

    @api.multi
    def on_change_partner_id(self, partner_id):
        """Recover trade name from partner if available."""
        result = super(Lead, self).on_change_partner_id(partner_id)

        if result.get("value"):
            if self.partner_id.comercial:
                result["value"]["trade_name"] = self.partner_id.comercial

        return result
