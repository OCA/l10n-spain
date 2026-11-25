# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import api, models


class ReportTransaherManifest(models.AbstractModel):
    _name = "report.delivery_transaher.report_transaher_manifest_document"
    _description = "Transaher Daily Manifest PDF Report"

    @api.model
    def _get_report_values(self, docids, data=None):
        data = dict(data or {})
        wizard_id = data.get("wizard_id") or (docids[0] if docids else False)
        docs = (
            self.env["transaher.manifest.wizard"].browse(wizard_id)
            if wizard_id
            else self.env["transaher.manifest.wizard"]
        )
        if not data.get("expeditions") and docs:
            data.update(docs[0]._prepare_report_data())
        return {
            "doc_ids": docs.ids,
            "doc_model": "transaher.manifest.wizard",
            "docs": docs,
            **data,
        }
