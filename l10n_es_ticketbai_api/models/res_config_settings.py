# Copyright 2021 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    tbai_enabled = fields.Boolean(related="company_id.tbai_enabled", readonly=True)
    tbai_device_serial_number = fields.Char(
        related="company_id.tbai_device_serial_number",
        string="Device Serial Number",
        readonly=False,
    )
