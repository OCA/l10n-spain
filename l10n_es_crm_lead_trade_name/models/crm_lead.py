# -*- coding: utf-8 -*-
# © 2015 Antiun Ingeniería, S.L.
# © 2017 QubiQ 2010, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from openerp import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    trade_name = fields.Char()

    @api.model
    def _lead_create_contact(self, lead, name, is_company, parent_id=False):
        """Add trade name to partner."""
        ctx = {"default_comercial": lead.trade_name}
        return (super(CrmLead, self.with_context(**ctx))
                ._lead_create_contact(lead, name, is_company, parent_id))

    @api.multi
    def on_change_partner_id(self, partner_id):
        """Recover trade name from partner if available."""
        result = super(CrmLead, self).on_change_partner_id(partner_id)
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            result["value"]["trade_name"] = partner.comercial
        return result
