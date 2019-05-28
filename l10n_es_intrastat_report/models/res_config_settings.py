# Copyright 2019 FactorLibre - Daniel Duque <daniel.duque@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    intrastat_state_id = fields.Many2one(
        comodel_name='res.country.state',
        related='company_id.intrastat_state_id')
