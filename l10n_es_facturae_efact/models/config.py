# Copyright 2017 Creu Blanca
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    efact_server = fields.Char(
        string="e.Fact server location",
        config_parameter='account.invoice.efact.server',
    )
    efact_port = fields.Char(
        string="e.Fact SSH port",
        config_parameter='account.invoice.efact.port',
    )
    efact_user = fields.Char(
        string="e.Fact user",
        config_parameter='account.invoice.efact.user',
    )
    efact_password = fields.Char(
        string="e.Fact password",
        config_parameter='account.invoice.efact.password',
    )
