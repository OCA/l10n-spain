# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import models, fields


class AeatModelExportConfig(models.Model):
    _name = 'aeat.model.export.config'

    name = fields.Char(string='Name')
    model_number = fields.Char(string='Model number', size=3)
    model_id = fields.Many2one(
        comodel_name='ir.model', string="Odoo model", oldname='model')
    date_start = fields.Date(string='Starting date')
    date_end = fields.Date(string='Ending date')
    config_line_ids = fields.One2many(
        comodel_name='aeat.model.export.config.line', oldname='config_lines',
        inverse_name='export_config_id', string='Lines')
