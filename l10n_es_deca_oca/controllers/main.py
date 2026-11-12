# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import http
from odoo.exceptions import AccessError, UserError
from odoo.http import content_disposition, request
from odoo.tools import consteq


class DecaController(http.Controller):
    @http.route(
        ["/my/picking/<int:picking_id>"], type="http", auth="public", methods=["GET"]
    )
    def public_delivery_portal(self, picking_id=None, access_token=None, **kw):
        picking = request.env["stock.picking"].sudo().browse(picking_id).exists()
        token = picking.deca_access_token if picking else False
        if (
            not token
            or not access_token
            or not consteq(token.encode(), access_token.encode())
        ):
            return request.make_response("Not Found", status=404)
        try:
            # A valid bearer authorizes only this report and this source company.
            with request.env.cr.savepoint():
                report = (
                    request.env["ir.actions.report"]
                    .sudo()
                    .with_company(picking.company_id)
                )
                pdf_content, _kind = report._render_qweb_pdf(
                    "l10n_es_deca_oca.report_deca", picking.id
                )
        except (AccessError, UserError):
            return request.make_response("Not Found", status=404)
        return request.make_response(
            pdf_content,
            headers=[
                ("Content-Type", "application/pdf"),
                (
                    "Content-Disposition",
                    content_disposition(f"DeCA - {picking.name}.pdf"),
                ),
                ("Cache-Control", "no-store"),
                ("X-Content-Type-Options", "nosniff"),
            ],
        )
