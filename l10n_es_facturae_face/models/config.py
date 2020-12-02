# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    face_server = fields.Char(
        string="FACe server location",
        config_parameter="account.invoice.face.server",
        required=True,
    )
