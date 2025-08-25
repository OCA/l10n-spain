# Copyright 2024 Aures TIC - Jose Zambudio
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    verifactu_enabled = fields.Boolean(
        compute="_compute_aeat_sending_enabled", string="VERI*FACTU enabled"
    )

    @api.depends("company_id")
    def _compute_aeat_sending_enabled(self):
        res = super()._compute_aeat_sending_enabled()
        verifactu_enabled = any(self.env.companies.mapped("verifactu_enabled"))
        for partner in self:
            partner.verifactu_enabled = (
                partner.company_id.verifactu_enabled
                if partner.company_id
                else verifactu_enabled
            )
            if partner.verifactu_enabled:
                partner.aeat_sending_enabled = True
        return res
