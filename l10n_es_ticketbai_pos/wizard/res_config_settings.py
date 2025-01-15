# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_tbai_device_serial_number = fields.Char(
        string="PoS TicketBAI Device Serial Number",
        related="pos_config_id.tbai_device_serial_number",
    )
    pos_tbai_certificate_id = fields.Many2one(
        related="pos_config_id.tbai_certificate_id",
        readonly=False,
    )
