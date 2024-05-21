# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pprint

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class SequraController(http.Controller):
    _webhook_url = "/payment/sequra/webhook"
    _notify_url = "/payment/sequra/notify"

    @http.route(_notify_url, type="http", auth="public", methods=["POST"], csrf=False)
    def sequra_return_from_checkout(self, **data):
        """Process the notification data sent by seQura.
        :param dict data: The notification data (only `id`)
                          and the transaction reference (`ref`)
                          embedded in the return URL
        """
        _logger.info(
            "handling notification from seQura with data:\n%s", pprint.pformat(data)
        )
        try:
            request.env["payment.transaction"].sudo()._handle_notification_data(
                "sequra", data
            )
        except ValidationError:  # Acknowledge the notification to avoid getting spammed
            _logger.exception(
                "unable to handle the notification data; skipping to acknowledge"
            )
        return ""  # Acknowledge the notification

    @http.route(_webhook_url, type="http", auth="public", methods=["POST"], csrf=False)
    def sequra_webhook(self, **data):
        """Process the request sent by seQura to the webhook.

        :param dict data: The notification data (only `id`)
                          and the transaction reference (`ref`)
                          embedded in the return URL
        :return: An empty string to acknowledge the notification
        :rtype: str
        """
        _logger.info(
            "webhook received from seQura with data:\n%s", pprint.pformat(data)
        )
        # We will. just acknowledge by now.
        return ""  # Acknowledge the notification
