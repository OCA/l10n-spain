# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if self._is_invoice_report(report_ref):
            self.env["account.move"].browse(res_ids)._check_external_invoice_output()
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
