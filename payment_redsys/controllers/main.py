# Copyright 2016-2017 Tecnativa - Sergio Teruel
# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# Copyright 2023 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pprint

from odoo import http
from odoo.http import request

from odoo.addons.payment.controllers.post_processing import PaymentPostProcessing

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
    def redsys_return(self, tx_ref=None, **post):
        """Redsys."""
        _logger.info(
            "Redsys: entering form_feedback with post data %s tx_ref=%s",
            pprint.pformat(post),
            tx_ref,
        )
        if post:
            request.env["payment.transaction"].sudo()._handle_notification_data(
                "redsys", post
            )
        # Re-attach the transaction to the user's session in case the
        # cross-site round-trip through Redsys dropped the session cookie
        # (browser SameSite policies behave differently on the POST/GET
        # combinations Redsys uses to redirect back to UrlOk).
        if tx_ref:
            tx = (
                request.env["payment.transaction"]
                .sudo()
                .search(
                    [("provider_code", "=", "redsys"), ("reference", "=", tx_ref)],
                    limit=1,
                )
            )
            if tx:
                PaymentPostProcessing.monitor_transactions(tx)
        # Always redirect to /payment/status so the user never gets a
        # blank page when Redsys delivers an empty GET to UrlOk (some
        # 3DS challenge flows do that when MerchantUrl == UrlOk and the
        # server-to-server notification has already been processed).
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
