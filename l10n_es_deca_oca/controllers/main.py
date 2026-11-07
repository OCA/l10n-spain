# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.http import request


class DecaController(http.Controller):
    @http.route(["/my/picking/<int:picking_id>"], type="http", auth="public")
    def public_delivery_portal(self, picking_id=None, access_token=None, **kw):
        if not picking_id:
            return request.make_response("Not Found", status=404)
        picking = request.env["stock.picking"].browse(picking_id)

        if (
            not picking.exists()
            or not access_token
            or picking.sudo().deca_access_token != access_token
        ):
            return request.make_response("Not Found", status=404)

        report = request.env["ir.actions.report"].sudo()
        pdf_content, _content_type = report._render_qweb_pdf(
            "l10n_es_deca_oca.report_deca", picking.id
        )
        file_name = f"DeCA - {picking.sudo().name}.pdf"
        return request.make_response(
            pdf_content,
            headers=[
                ("Content-Type", "application/pdf"),
                ("Content-Disposition", f'attachment; filename="{file_name}"'),
            ],
        )
