# -*- coding: utf-8 -*-
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from openerp import models, fields, api, _


class AeatModelExportConfig(models.Model):

    _name = 'aeat.model.export.config'

    name = fields.Char(string='Name')
    model_number = fields.Char(string='Model number', size=3)
    model = fields.Many2one('ir.model', 'Odoo model')
    date_start = fields.Date(string='Start date')
    date_end = fields.Date(string='End date')
    config_lines = fields.One2many(
        comodel_name='aeat.model.export.config.line',
        inverse_name='export_config_id', string='Lines')


class AeatModelExportConfigLine(models.Model):
    _name = 'aeat.model.export.config.line'
    _order = 'sequence'

    sequence = fields.Integer("Sequence")
    export_config_id = fields.Many2one(
        comodel_name='aeat.model.export.config', string='Config parent',
        ondelete="cascade", required=True)
    name = fields.Char(string="Name", required=True)
    repeat_expression = fields.Char(
        string='Repeat expression',
        help="If set, this expression will be used for getting the list of "
             "elements to iterate on")
    repeat = fields.Boolean(compute='_compute_repeat', store=True)
    conditional_expression = fields.Char(
        string='Conditional expression',
        help="If set, this expression will be used to evaluate if this line "
             "should be added")
    conditional = fields.Boolean(compute='_compute_conditional', store=True)
    sub_config = fields.Many2one(
        comodel_name='aeat.model.export.config', string='Sub-configuration')
    export_type = fields.Selection(
        selection=[('string', 'Alphanumeric'),
                   ('float', 'Number with decimals'),
                   ('integer', 'Number without decimals'),
                   ('boolean', 'Boolean'),
                   ('subconfig', 'Sub-configuration')],
        default='string', string="Export field type", required=True)
    apply_sign = fields.Boolean("Apply sign", default=True)
    positive_sign = fields.Char("Positive sign character", size=1, default='0')
    negative_sign = fields.Char(
        "Negative sign character", size=1, default='N', oldname='sign')
    size = fields.Integer("Field size")
    alignment = fields.Selection(
        [('left', 'Left'), ('right', 'Right')],
        default='left', string="Alignment")
    bool_no = fields.Char("Value for no", size=1, default=' ')
    bool_yes = fields.Char("Value for yes", size=1, default='X')
    decimal_size = fields.Integer("Number of char for decimals", default=0)
    expression = fields.Char('Expression')
    fixed_value = fields.Char('Fixed value')
    position = fields.Integer(compute='_compute_position')
    value = fields.Char(compute='_compute_value', store=True)

    @api.one
    @api.depends('repeat_expression')
    def _compute_repeat(self):
        self.repeat = bool(self.repeat_expression)

    @api.one
    @api.depends('conditional_expression')
    def _compute_conditional(self):
        self.conditional = bool(self.conditional_expression)

    @api.one
    @api.depends('sequence')
    def _compute_position(self):
        # TODO: Take into account sub-configurations
        self.position = 1
        for line in self.export_config_id.config_lines:
            if line == self:
                break
            self.position += line.size

    @api.one
    @api.depends('fixed_value', 'expression')
    def _compute_value(self):
        if self.export_type == 'subconfig':
            self.value = '-'
        elif self.expression:
            self.value = _('Expression: ')
            if len(self.expression) > 35:
                self.value += u'"%s…"' % self.expression[:34]
            else:
                self.value += u'"%s"' % self.expression
        else:
            self.value = _('Fixed: %s') % (self.fixed_value or _('<blank>'))

    @api.one
    @api.onchange('export_type')
    def onchange_type(self):
        if self.export_type in ('float', 'integer'):
            self.alignment = 'right'
        elif self.export_type in ('string', 'boolean'):
            self.alignment = 'left'

    @api.one
    @api.onchange('sub_config')
    def onchange_subconfig(self):
        if self.sub_config:
            self.export_type = False
            self.decimal_size = 0
            self.alignment = False
            self.apply_sign = False
