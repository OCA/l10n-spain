# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from openerp import models, fields, api


class AeatModelExportConfig(models.Model):

    _name = 'aeat.model.export.config'

    name = fields.Char(string='Name')
    model_number = fields.Char(string='Model number', size=3)
    model = fields.Many2one('ir.model', 'Odoo Model')
    date_start = fields.Date(string='Start date')
    date_end = fields.Date(string='End date')
    config_lines = fields.One2many('aeat.model.export.config.line',
                                   'export_config_id', string='Lines')


class AeatModelExportConfigLine(models.Model):

    _name = 'aeat.model.export.config.line'
    _order = 'sequence'

    sequence = fields.Integer("Sequence")
    export_config_id = fields.Many2one('aeat.model.export.config',
                                       string='Config parent')
    name = fields.Char(string="Name")
    repeat = fields.Boolean(string='Repeat')
    sub_config = fields.Many2one('aeat.model.export.config', 'Subconfig')
    position = fields.Integer("First character position")
    export_type = fields.Selection([('string', 'Alphanumeric'),
                                    ('float', 'Number with decimals'),
                                    ('integer', 'Number without decimals'),
                                    ('boolean', 'Boolean')], default='string',
                                   string="Export field type")
    apply_sign = fields.Boolean("Apply sign")
    sign = fields.Char("Sign character", size=1, default='N')
    size = fields.Integer("Field size")
    alignment = fields.Selection([('left', 'Left'), ('right', 'Right')],
                                 default='left', string="Alignment")
    bool_no = fields.Char("No value", size=1, default=' ')
    bool_yes = fields.Char("Yes value", size=1, default='X')
    decimal_size = fields.Integer("Number of char for decimals", default=0)
    expression = fields.Text('Expression')
    fixed_value = fields.Char('Fixed Value')

    @api.one
    @api.onchange('export_type')
    def onchange_type(self):
        if self.export_type:
            self.sub_config = False
            self.repeat = False
            if self.export_type == 'float':
                self.decimal_size = 2
                self.alignment = 'right'
            elif self.export_type == 'integer':
                self.decimal_size = 0
                self.alignment = 'right'
            elif self.export_type in ('string', 'boolean'):
                self.alignment = 'left'
                self.decimal_size = 0
                self.apply_sign = False

    @api.one
    @api.onchange('sub_config')
    def onchange_subconfig(self):
        if self.sub_config:
            self.export_type = False
            self.decimal_size = 0
            self.alignment = False
            self.apply_sign = False
