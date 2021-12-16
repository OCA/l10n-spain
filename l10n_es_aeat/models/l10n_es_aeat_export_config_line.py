# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2014-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import _, api, fields, models


class AeatModelExportConfigLine(models.Model):
    _name = "aeat.model.export.config.line"
    _order = "sequence"
    _description = "AEAT export configuration line"

    sequence = fields.Integer()
    export_config_id = fields.Many2one(
        comodel_name="aeat.model.export.config",
        string="Config parent",
        ondelete="cascade",
        required=True,
    )
    name = fields.Char(required=True)
    repeat_expression = fields.Char(
        help="If set, this expression will be used for getting the list of "
        "elements to iterate on",
    )
    repeat = fields.Boolean(compute="_compute_repeat", store=True)
    conditional_expression = fields.Char(
        help="If set, this expression will be used to evaluate if this line "
        "should be added",
    )
    conditional = fields.Boolean(compute="_compute_conditional", store=True)
    subconfig_id = fields.Many2one(
        comodel_name="aeat.model.export.config", string="Sub-configuration"
    )
    export_type = fields.Selection(
        selection=[
            ("string", "Alphanumeric"),
            ("alphabetic", "Alphabetic"),
            ("float", "Number with decimals"),
            ("integer", "Number without decimals"),
            ("boolean", "Boolean"),
            ("subconfig", "Sub-configuration"),
        ],
        default="string",
        string="Export field type",
        required=True,
    )
    apply_sign = fields.Boolean(
        compute="_compute_apply_sign", readonly=False, store=True
    )
    positive_sign = fields.Char(string="Positive sign character", size=1, default="0")
    negative_sign = fields.Char(string="Negative sign character", size=1, default="N")
    size = fields.Integer(string="Field size")
    alignment = fields.Selection(
        selection=[("left", "Left"), ("right", "Right")],
        compute="_compute_alignment",
        readonly=False,
        store=True,
    )
    bool_no = fields.Char(string="Value for no", size=1, default=" ")
    bool_yes = fields.Char(string="Value for yes", size=1, default="X")
    decimal_size = fields.Integer(
        string="Number of char for decimals",
        compute="_compute_decimal_size",
        readonly=False,
        store=True,
    )
    expression = fields.Char()
    fixed_value = fields.Char()
    position = fields.Integer(compute="_compute_position")
    value = fields.Char(compute="_compute_value", store=True)

    @api.depends("repeat_expression")
    def _compute_repeat(self):
        for line in self:
            line.repeat = bool(line.repeat_expression)

    @api.depends("conditional_expression")
    def _compute_conditional(self):
        for line in self:
            line.conditional = bool(line.conditional_expression)

    def _size_get(self, lines):
        size = 0
        for line in lines:
            if line.export_type == "subconfig":
                size += self._size_get(line.subconfig_id.config_line_ids)
            else:
                size += line.size
        return size

    @api.depends("sequence")
    def _compute_position(self):
        for line in self:
            line.position = 1
            for line2 in line.export_config_id.config_line_ids:
                if line2 == line:
                    break
                line.position += line._size_get(line2)

    @api.depends("fixed_value", "expression")
    def _compute_value(self):
        for line in self:
            if line.export_type == "subconfig":
                line.value = "-"
            elif line.expression:
                line.value = _("Expression: ")
                if len(line.expression) > 35:
                    line.value += '"%s…"' % line.expression[:34]
                else:
                    line.value += '"%s"' % line.expression
            else:
                line.value = _("Fixed: {}").format(line.fixed_value or _("<blank>"))

    @api.depends("export_type", "subconfig_id")
    def _compute_alignment(self):
        for line in self:
            if line.subconfig_id:
                line.alignment = False
            else:
                if line.export_type in ("float", "integer"):
                    line.alignment = "right"
                elif line.export_type in ("string", "boolean"):
                    line.alignment = "left"
                else:
                    line.alignment = line.alignment or "left"

    @api.depends("subconfig_id")
    def _compute_apply_sign(self):
        for line in self:
            line.apply_sign = line.apply_sign or True
            if self.subconfig_id:
                self.apply_sign = False

    @api.depends("subconfig_id")
    def _compute_decimal_size(self):
        for line in self:
            line.decimal_size = line.decimal_size or 0
            if self.subconfig_id:
                self.decimal_size = 0
