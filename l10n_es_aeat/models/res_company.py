# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, models


class ResCompany(models.Model):
    _inherit = "res.company"

    @api.model
    def create(self, values):
        """Create immediately all the AEAT sequences when creating company."""
        company = super().create(values)
        models = self.env['ir.model'].search([
            ('model', '=like', 'l10n.es.aeat.%.report'),
        ])
        for model in models:
            try:
                self.env[model.model]._register_hook(companies=company)
            except Exception:
                pass
        return company
