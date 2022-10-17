# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class L10nEsAeatReportExportToBoe(models.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"

    def _export_line_process(self, obj, line):
        val = super(L10nEsAeatReportExportToBoe, self)._export_line_process(obj, line)
        if line.line_crlf:
            val += b"\r\n"
        return val
