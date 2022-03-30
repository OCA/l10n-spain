# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import logging

from odoo import _, api, exceptions, fields, models
from odoo.tools.safe_eval import safe_eval

_logger = logging.getLogger(__name__)


class L10nEsAeatReportExportToBoe(models.TransientModel):
    _name = "l10n.es.aeat.report.compare_boe_file"
    _description = "Compare BOE file wizard"

    data = fields.Binary(string="File", required=True)
    state = fields.Selection(
        selection=[("open", "open"), ("compare", "compare")],
        default="open",
    )
    line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.report.compare_boe_file.line",
        inverse_name="wizard_id",
        string="Lines",
    )

    def _compare_boe_lines(self, config, data, offset=0):
        lines = []
        for line in config.config_line_ids:
            if line.conditional_expression:
                # Try to evaluate condition to see if it's not report dependent
                if not safe_eval(line.conditional_expression):
                    continue
            if line.export_type == "subconfig":
                offset, sub_lines = self._compare_boe_lines(
                    line.subconfig_id, data, offset=offset
                )
                lines += sub_lines
            else:
                lines.append(
                    (
                        0,
                        0,
                        {
                            "wizard_id": self.id,
                            "export_line_id": line.id,
                            "content": data[offset : offset + line.size],
                        },
                    )
                )
                offset += line.size
        return offset, lines

    def button_compare_file(self):
        """Method that compares a file against a BOE export config.

        @return: Action dictionary for showing comparison.
        """
        self.ensure_one()
        active_id = self.env.context.get("active_id", False)
        active_model = self.env.context.get("active_model", False)
        if not active_id or not active_model:
            return False
        config = self.env[active_model].browse(active_id)
        data = base64.decodebytes(self.data)
        offset, lines = self._compare_boe_lines(config, data)
        # Allow a bit of difference according presence of final CR+LF
        if abs(offset - len(data)) > 2:
            raise exceptions.UserError(
                _(
                    "The length of the file is different from the expected one, "
                    "or there are conditional parts in the export configuration "
                    "that can't be evaled statically."
                )
            )
        self.write({"line_ids": lines, "state": "compare"})
        res = self.env.ref("l10n_es_aeat.action_wizard_compare_boe_file").read()[0]
        res["res_id"] = self.id
        return res


class L10nEsAeatReportExportToBoeLine(models.TransientModel):
    _name = "l10n.es.aeat.report.compare_boe_file.line"
    _description = "Compare BOE file wizard"

    wizard_id = fields.Many2one(
        comodel_name="l10n.es.aeat.report.compare_boe_file",
        string="Wizard",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    export_line_id = fields.Many2one(
        comodel_name="aeat.model.export.config.line",
        string="Export line",
        required=True,
        readonly=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(
        string="Sequence", related="export_line_id.sequence", readonly=True
    )
    name = fields.Char(string="Name", related="export_line_id.name", readonly=True)
    content = fields.Char()
    content_float = fields.Float(compute="_compute_content_float", string="Amount")

    @api.depends("content")
    def _compute_content_float(self):
        self.content_float = False
        for line in self.filtered(lambda x: x.export_line_id.export_type == "float"):
            content = line.content
            sign = 1
            if line.export_line_id.apply_sign:
                if content[0] == line.export_line_id.negative_sign:
                    content = content[1:]
                    sign = -1
            if line.export_line_id.decimal_size:
                try:
                    line.content_float = sign * (
                        float(content) / 10**line.export_line_id.decimal_size
                    )
                except Exception as e:
                    _logger.debug(e)
            else:
                line.content_float = sign * line.content
