# Copyright 2024 Aures TIC - Jose Zambudio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    verifactu_enabled = fields.Boolean(
        compute="_compute_verifactu_enabled",
    )

    @api.depends("company_id")
    def _compute_verifactu_enabled(self):
        verifactu_enabled = any(self.env.companies.mapped("verifactu_enabled"))
        for partner in self:
            partner.verifactu_enabled = (
                partner.company_id.verifactu_enabled
                if partner.company_id
                else verifactu_enabled
            )
