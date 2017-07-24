# -*- coding: utf-8 -*-
# © 2017 Creu Blanca
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    efact_server = fields.Char(string="e.Fact server location")
    efact_port = fields.Char(string="e.Fact SSH port")
    efact_user = fields.Char(string="e.Fact user")
    efact_password = fields.Char(string="e.Fact password")

    @api.model
    def get_default_efact_server(self, fields):
        face_server = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.server", default=None)
        return {'efact_server': face_server or False}

    @api.multi
    def set_efact_server(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                "account.invoice.efact.server", record.efact_server or '')

    @api.model
    def get_default_efact_port(self, fields):
        efact_port = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.port", default=None)
        return {'efact_port': efact_port or False}

    @api.multi
    def set_efact_port(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                "account.invoice.efact.port", record.efact_port or '')

    @api.model
    def get_default_efact_user(self, fields):
        efact_user = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.user", default=None)
        return {'efact_user': efact_user or False}

    @api.multi
    def set_efact_user(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                "account.invoice.efact.user", record.efact_user or '')

    @api.model
    def get_default_efact_password(self, fields):
        efact_password = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.password", default=None)
        return {'efact_password': efact_password or False}

    @api.multi
    def set_efact_password(self):
        for record in self:
            self.env['ir.config_parameter'].set_param(
                "account.invoice.efact.password", record.efact_password or '')
