# Part of Odoo. See LICENSE file for full copyright and licensing details.

import base64
import logging
import pprint

import requests
from werkzeug import urls

from odoo import _, api, fields, models, service
from odoo.exceptions import ValidationError

from .. import const

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("sequra", "seQura")], ondelete={"sequra": "set default"}
    )
    sequra_user = fields.Char(
        string="API Username",
        help="The Test or Live API username depending on the configuration "
        + "of the provider",
        required_if_provider="sequra",
        groups="base.group_system",
    )
    sequra_pass = fields.Char(
        string="API Password",
        help="The Test or Live API password depending on the configuration "
        + "of the sequra_user",
        required_if_provider="sequra",
        groups="base.group_system",
    )
    sequra_merchant = fields.Char(
        string="Merchant ref",
        help="The merchant reference",
        required_if_provider="sequra",
        groups="base.group_system",
    )

    sequra_endpoint = fields.Char(
        string="seQura Endpoint",
        compute="_compute_sequra_endpoint",
        help="The endpoint of the seQura API",
        store=False,
    )

    @api.depends("state")
    def _compute_sequra_endpoint(self):
        for record in self:
            if record.state == "enabled":
                record.sequra_endpoint = "https://live.sequrapi.com"
            else:
                record.sequra_endpoint = "https://sandbox.sequrapi.com"

    # === BUSINESS METHODS ===#

    def _get_supported_currencies(self):
        """Override of `payment` to return the supported currencies."""
        supported_currencies = super()._get_supported_currencies()
        if self.code == "sequra":
            supported_currencies = supported_currencies.filtered(
                lambda c: c.name in const.SUPPORTED_CURRENCIES
            )
        return supported_currencies

    def _sequra_make_request(self, endpoint, data=None, params=None, method="POST"):
        """Make a request at sequra endpoint.

        Note: self.ensure_one()

        :param str endpoint: The endpoint to be reached by the request
        :param dict data: The payload of the request
        :param str method: The HTTP method of the request
        :return The JSON-formatted content of the response
        :rtype: dict
        :raise: ValidationError if an HTTP error occurs
        """
        self.ensure_one()
        url = urls.url_join(self.sequra_endpoint, endpoint)

        odoo_version = service.common.exp_version()["server_version"]
        module_version = self.env.ref("base.module_payment_sequra").installed_version
        headers = {
            "Authorization": "basic "
            + base64.b64encode(
                f"{self.sequra_user}:{self.sequra_pass}".encode()
            ).decode("utf-8"),
            "User-Agent": f"Odoo/{odoo_version} seQuraOdoo/{module_version}",
        }
        if method == "POST":
            headers["Content-Type"] = "application/json"
            headers["Accept"] = "application/json"
        try:
            response = requests.request(
                method, url, json=data, headers=headers, params=params, timeout=60
            )
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError:
                _logger.exception(
                    "Invalid API request at %s with data:\n%s",
                    url,
                    pprint.pformat(data),
                )
                raise ValidationError(
                    _(
                        "seQura: The communication with the API failed."
                        + "seQura gave us the following "
                        + "information: %s",
                        response.json().get("errors", "")
                        or (url + " " + str(response.status_code)),
                    )
                ) from None
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            _logger.exception("Unable to reach endpoint at %s", url)
            raise ValidationError(
                _("seQura: Could not establish the connection to the API.")
            ) from None
        return response
