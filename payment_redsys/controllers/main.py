# Copyright 2016-2017 Tecnativa - Sergio Teruel
# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pprint

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class RedsysController(http.Controller):
    _return_url = "/payment/redsys/return"
    _cancel_url = "/payment/redsys/cancel"
    _exception_url = "/payment/redsys/error"
    _reject_url = "/payment/redsys/reject"

    @http.route(
        [
            "/payment/redsys/return",
            "/payment/redsys/cancel",
            "/payment/redsys/error",
            "/payment/redsys/reject",
        ],
        type="http",
        auth="public",
        csrf=False,
    )
    def redsys_return(self, **post):
        """Redsys."""
        _logger.info(
            "Redsys: entering form_feedback with post data %s", pprint.pformat(post)
        )
        if post:
            request.env["payment.transaction"].sudo()._handle_notification_data(
                "redsys", post
            )
            return request.redirect("/payment/status")

    @http.route(
        ["/payment/redsys/result/<page>"],
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
    )
    def redsys_result(self, page, **vals):
        return request.redirect("/payment/status")
