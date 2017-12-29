# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    face_server = fields.Char(string="FACe server location")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        face_server = self.env["ir.config_parameter"].get_param(
            "account.invoice.face.server", default=None)
        res.update(face_server=face_server)
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            "account.invoice.face.server", self.face_server or '')
