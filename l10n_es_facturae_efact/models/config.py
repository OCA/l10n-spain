# © 2017 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    efact_server = fields.Char(string="e.Fact server location")
    efact_port = fields.Char(string="e.Fact SSH port")
    efact_user = fields.Char(string="e.Fact user")
    efact_password = fields.Char(string="e.Fact password")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        efact_server = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.server", default=None)
        efact_port = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.port", default=None)
        efact_user = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.user", default=None)
        efact_password = self.env["ir.config_parameter"].get_param(
            "account.invoice.efact.password", default=None)
        res.update({
            'efact_server': efact_server,
            'efact_port': efact_port,
            'efact_user': efact_user,
            'efact_password': efact_password,
        })
        return res

    @api.multi
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].set_param(
            "account.invoice.efact.server", self.efact_server or '')
        self.env['ir.config_parameter'].set_param(
            "account.invoice.efact.port", self.efact_port or '')
        self.env['ir.config_parameter'].set_param(
            "account.invoice.efact.user", self.efact_user or '')
        self.env['ir.config_parameter'].set_param(
            "account.invoice.efact.password", self.efact_password or '')
