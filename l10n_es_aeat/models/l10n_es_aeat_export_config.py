# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import fields, models


class AeatModelExportConfig(models.Model):
    _name = "aeat.model.export.config"
    _description = "AEAT export configuration"
    _order = "name"

    name = fields.Char(string="Name")
    model_number = fields.Char(string="Model number", size=3)
    model_id = fields.Many2one(comodel_name="ir.model", string="Odoo model")
    active = fields.Boolean(default=True)
    date_start = fields.Date(string="Starting date")
    date_end = fields.Date(string="Ending date")
    config_line_ids = fields.One2many(
        comodel_name="aeat.model.export.config.line",
        inverse_name="export_config_id",
        string="Lines",
    )
