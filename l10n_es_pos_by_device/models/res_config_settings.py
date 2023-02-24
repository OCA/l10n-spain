# Copyright 2023 Landoo Sistemas de Informacion SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_sequence_by_device = fields.Boolean(
        related="company_id.pos_sequence_by_device", readonly=False
    )
