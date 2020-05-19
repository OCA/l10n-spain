# Copyright 2016-2017 Sergio Teruel <sergio.teruel@tecnativa.com>
# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
import pprint

import werkzeug

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
        auth="none",
        csrf=False,
    )
    def redsys_return(self, **post):
        """ Redsys."""
        _logger.debug(
            "Redsys: entering form_feedback with post data %s", pprint.pformat(post)
        )
        if post:
            request.env["payment.transaction"].sudo().form_feedback(post, "redsys")
        return_url = post.pop("return_url", "")
        if not return_url:
            return_url = "/shop"
        return werkzeug.utils.redirect(return_url)

    @http.route(
        ["/payment/redsys/result/<page>"],
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
    )
    def redsys_result(self, page, **vals):
        return werkzeug.utils.redirect("/payment/process")
