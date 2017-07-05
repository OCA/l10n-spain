# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    face_server = fields.Char(string="FACe server location")

    @api.model
    def get_default_face_server(self, fields):
        face_server = self.env["ir.config_parameter"].get_param(
            "account.invoice.face.server", default=None)
        return {'face_server': face_server or False}

    @api.multi
    def set_face_server(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                "account.invoice.face.server", record.face_server or '')
