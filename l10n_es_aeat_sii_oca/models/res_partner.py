# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sii_enabled = fields.Boolean(
        compute="_compute_sii_enabled",
    )
    sii_simplified_invoice = fields.Boolean(
        string="Simplified invoices in SII?",
        help="Checking this mark, invoices done to this partner will be "
             "sent to SII as simplified invoices."
    )

    @api.multi
    def _compute_sii_enabled(self):
        sii_enabled = self.env.user.company_id.sii_enabled
        for partner in self:
            partner.sii_enabled = sii_enabled
