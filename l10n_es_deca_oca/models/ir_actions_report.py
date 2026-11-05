# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io

from odoo import fields, models
from odoo.tools.pdf import PdfFileReader, PdfWriter, merge_pdf


class IrActionsReport(models.Model):
    _inherit = "ir.actions.report"

    def _render_qweb_html(self, report_ref, docids, data=None):
        report = self._get_report(report_ref)
        if report.report_name == "l10n_es_deca_oca.report_deca" and docids:
            pickings = self.env["stock.picking"].browse(
                [docids] if isinstance(docids, int) else docids
            )
            pickings._check_deca_access()
            pickings._check_deca_required_fields()
        return super()._render_qweb_html(report_ref, docids, data=data)

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        report = self._get_report(report_ref)
        if report.report_name != "l10n_es_deca_oca.report_deca" or not res_ids:
            return super()._render_qweb_pdf(report_ref, res_ids, data)
        if isinstance(res_ids, int):
            res_ids = [res_ids]
        pickings = self.env["stock.picking"].browse(res_ids)
        pickings._check_deca_access()
        pickings._check_deca_required_fields()
        documents = []
        for picking in pickings:
            renderer = self.with_company(picking.company_id).with_context(
                lang=picking.partner_id.lang
                or picking.company_id.partner_id.lang
                or "en_US",
                tz=picking.company_id.partner_id.tz or "UTC",
                force_report_rendering=True,
                report_pdf_no_attachment=True,
            )
            documents.append(renderer._render_deca_version(report_ref, picking, data))
        return (documents[0] if len(documents) == 1 else merge_pdf(documents)), "pdf"

    def _render_deca_version(self, report_ref, picking, data):
        """Reuse only the protected current version, never a filename match."""
        picking = picking.with_env(self.env)
        current_hash = picking._get_deca_hash()
        attachment = picking.deca_attachment_id.sudo()
        if (
            attachment
            and attachment.deca_source_id == picking.id
            and attachment.deca_version == picking.deca_version
            and attachment.deca_content_hash
            == current_hash
            == picking.deca_content_hash
        ):
            return attachment.raw

        # Flush before rendering/creating the file: competing issuers serialize on
        # the picking row; native request handling retries serialization failures.
        version = picking.deca_version + 1
        first_date = picking.deca_first_version_date or fields.Datetime.now()
        picking.sudo().write(
            {
                "deca_version": version,
                "deca_first_version_date": first_date,
                "deca_content_hash": current_hash,
            }
        )
        picking.flush_recordset(
            ["deca_version", "deca_first_version_date", "deca_content_hash"]
        )
        content, _kind = super()._render_qweb_pdf(report_ref, picking.ids, data)
        reader = PdfFileReader(io.BytesIO(content), strict=False)
        writer = PdfWriter()
        writer.appendPagesFromReader(reader)
        metadata = {
            key: str(value)
            for key, value in (reader.getDocumentInfo() or {}).items()
            if value is not None
        }
        metadata.update(
            {
                "/CreationDate": first_date.strftime("D:%Y%m%d%H%M%SZ"),
                "/ModDate": fields.Datetime.now().strftime("D:%Y%m%d%H%M%SZ"),
            }
        )
        writer.addMetadata(metadata)
        output = io.BytesIO()
        writer.write(output)
        content = output.getvalue()
        attachment = (
            self.env["ir.attachment"]
            .sudo()
            .create(
                {
                    "name": f"DeCA - {picking.name} - v{version}.pdf",
                    "type": "binary",
                    "raw": content,
                    "mimetype": "application/pdf",
                    "res_model": "stock.picking",
                    "res_id": picking.id,
                    "company_id": picking.company_id.id,
                    "deca_source_id": picking.id,
                    "deca_version": version,
                    "deca_content_hash": current_hash,
                }
            )
        )
        picking.sudo().deca_attachment_id = attachment
        return content
