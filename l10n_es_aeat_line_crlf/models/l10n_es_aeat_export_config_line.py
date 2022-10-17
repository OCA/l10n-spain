# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AeatModelExportConfigLine(models.Model):
    _inherit = "aeat.model.export.config.line"

    line_crlf = fields.Boolean(string="Line CRLF")
