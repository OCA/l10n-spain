# -*- coding: utf-8 -*-
# Copyright 2015 Antiun Ingeniería, S.L.
# Copyright 2017 QubiQ 2010, S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    trade_name = fields.Char()

    def _lead_create_contact(self, name, is_company, parent_id=False):
        """Add trade name to partner."""
        ctx = {"default_comercial": self.trade_name}
        return (super(CrmLead, self.with_context(**ctx))
                ._lead_create_contact(name, is_company, parent_id))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Recover trade name from partner if available."""
        values = self._onchange_partner_id_values(
            self.partner_id.id if self.partner_id else False)
        if self.partner_id:
            values["trade_name"] = self.partner_id.comercial
        self.update(values)
