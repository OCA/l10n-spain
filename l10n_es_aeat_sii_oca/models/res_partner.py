# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    sii_enabled = fields.Boolean(
        compute="_compute_aeat_sending_enabled",
    )

    @api.depends("company_id")
    def _compute_aeat_sending_enabled(self):
        res = super()._compute_aeat_sending_enabled()
        sii_enabled = any(self.env.companies.mapped("sii_enabled"))
        for partner in self:
            sii_enabled = (
                partner.company_id.sii_enabled if partner.company_id else sii_enabled
            )
            partner.sii_enabled = sii_enabled
            if sii_enabled:
                partner.aeat_sending_enabled = True
        return res
