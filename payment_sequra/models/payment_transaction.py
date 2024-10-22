# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hashlib
import logging
import os
import pprint

import pytz
from werkzeug import urls

from odoo import _, api, fields, models, service
from odoo.exceptions import ValidationError
from odoo.http import request

from ..controllers.main import SequraController

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        """Override of payment to return seQura-specific rendering values.

        Note: self.ensure_one() from `_get_processing_values`

        :param dict processing_values: The generic and specific processing
                                        values of the transaction
        :return: The dict of provider-specific rendering values
        :rtype: dict
        """
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "sequra":
            return res
        payload = self._sequra_prepare_payment_request_payload(
            processing_values["reference"]
        )
        if not payload:
            return res
        _logger.info("Starting solicitation:\n%s", pprint.pformat(payload))
        solicitation_response = self.provider_id._sequra_make_request(
            "/orders", data=payload
        )
        self.provider_reference = solicitation_response.headers.get("Location").split(
            "/"
        )[-1]
        rendering_values = {
            "api_url": solicitation_response.headers.get("Location") + "/embedded_form",
            "product": "pp3",
        }
        _logger.info("Starting rendering_values:\n%s", pprint.pformat(rendering_values))
        return rendering_values

    def _sequra_prepare_payment_request_payload(self, reference, state=""):
        """Create the payload for the payment request based on the transaction values.

        :return: The request payload
        :rtype: dict
        """
        order_name = reference[: reference.rfind("-")]
        order = self.env["sale.order"].search([("name", "=", order_name)])
        if not order:
            return False
        base_url = self.provider_id.get_base_url()
        return_url = urls.url_join(
            base_url,
            f"/my/orders/{order.id}?{urls.url_encode(request.httprequest.args)}",
        )
        webhook_url = urls.url_join(base_url, SequraController._webhook_url)
        notify_url = urls.url_join(base_url, SequraController._notify_url)
        return {
            "order": {
                "state": state,
                "merchant": {
                    "id": self.provider_id.sequra_merchant,
                    "notify_url": notify_url,
                    "return_url": return_url,
                    "abort_url": return_url,
                    "notification_parameters": {
                        "order_id": str(order.id),
                        "signature": self._sequra_generate_signature(order),
                    },
                    "events_webhook": {
                        "url": webhook_url,
                        "parameters": {
                            "order_id": str(order.id),
                            "signature": self._sequra_generate_signature(order),
                        },
                    },
                },
                "merchant_reference": {
                    "order_ref_1": reference,
                },
                "cart": {
                    "cart_ref": order.name,
                    "currency": self.currency_id.name or "EUR",
                    "items": self._get_items(order, ""),
                    "order_total_with_tax": int(round((order.amount_total) * 100, 2)),
                    "gift": False,
                },
                "delivery_address": self._get_address(order.partner_shipping_id),
                "invoice_address": self._get_address(order.partner_invoice_id),
                "customer": self._get_customer_data(order.partner_id, order),
                "delivery_method": {
                    "name": "no shipping",  # @todo
                },
                "gui": {
                    "layout": "desktop",  # @todo
                },
                "platform": {
                    "name": "Odoo",
                    "version": service.common.exp_version()["server_version"],
                    "uname": " ".join(os.uname()),
                    "db_name": "postgresql",
                    "db_version": "N/A",
                },
            }
        }

    def _get_address(self, partner_id):
        def _partner_split_name(partner_name):
            return [
                " ".join(partner_name.split()[:-1]),
                " ".join(partner_name.split()[-1:]),
            ]

        return {
            "given_names": _partner_split_name(partner_id.name)[1],
            "surnames": _partner_split_name(partner_id.name)[0],
            "company": partner_id.company_id.name or "",
            "address_line_1": partner_id.street or "",
            "address_line_2": partner_id.street2 or "",
            "postal_code": partner_id.zip or "",
            "city": partner_id.city or "",
            "country_code": partner_id.country_id.code or "",
            "phone": partner_id.phone or "",
            "mobile_phone": partner_id.mobile or "",
            "nin": (partner_id.vat and partner_id.vat[2:]) or "",
        }

    @api.model
    def _get_customer_data(self, partner_id, order):
        order_ids = (
            self.env["sale.order"]
            .sudo()
            .search(
                [("partner_id", "=", partner_id.id), ("id", "!=", order.id)],
                limit=10,
                order="create_date desc",
            )
        )

        previous_orders = [
            {
                "created_at": fields.Datetime.from_string(o.create_date)
                .replace(
                    tzinfo=pytz.timezone(o.partner_id.tz or "Europe/Madrid"),
                    microsecond=0,
                )
                .isoformat(),
                "amount": int(round(o.amount_total * 100, 2)),
                "currency": o.currency_id.name,
            }
            for o in order_ids
        ]
        if "HTTP_X_FORWARDED_FOR" in request.httprequest.environ:
            ip_number = request.httprequest.environ["HTTP_X_FORWARDED_FOR"]
        elif "HTTP_HOST" in request.httprequest.environ:
            ip_number = request.httprequest.environ["REMOTE_ADDR"]
        customer = self._get_address(partner_id)
        customer["email"] = partner_id.email or ""
        customer["language_code"] = (
            self.env.context.get("lang") or partner_id.lang or ""
        )
        customer["ref"] = partner_id.id
        customer["company"] = partner_id.company_id.name or ""
        customer["logged_in"] = "unknown"
        customer["ip_number"] = ip_number
        customer["user_agent"] = request.httprequest.environ["HTTP_USER_AGENT"]
        customer["vat_number"] = partner_id.company_id.vat or ""
        customer["previous_orders"] = previous_orders

        return customer

    @api.model
    def _sequra_generate_signature(self, order):
        """Generate the signature for the order.

        :return: The generated signature
        :rtype: str
        """
        return hashlib.sha256(
            f"{order.id}{self.provider_id.sequra_pass}".encode("utf-8")
        ).hexdigest()

    def _get_items(self, order, shipping_name="N/A"):
        """Return the items of the order.

        :param recordset of `sale.order` order: The order
        :param str currency: The currency of the order
        :return: The items of the order
        :rtype: list of dict
        """
        items = []
        for line in order.order_line:
            total_with_tax = int(round((line.price_total) * 100, 2))
            price_with_tax = int(round((total_with_tax / line.product_uom_qty), 2))
            item = {
                "type": "product",
                "reference": str(line.product_id.id),
                "name": line.name,
                "quantity": int(line.product_uom_qty),
                "price_with_tax": price_with_tax,
                "total_with_tax": total_with_tax,
                "downloadable": False,
            }
            if line.product_id.type == "service":
                item["type"] = "service"
                item["ends_in"] = line.product_id.ends_in
            # @todo find a way to detect shipping cost type products
            items.append(item)
        return items

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        """Override of payment to find the transaction based on seQura data.

        :param str provider_code: The code of the provider that handled the transaction
        :param dict notification_data: The notification data sent by the provider
        :return: The transaction if found
        :rtype: recordset of `payment.transaction`
        :raise: ValidationError if the data match no transaction
        """
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "sequra" or len(tx) == 1:
            return tx

        tx = self.search(
            [
                ("reference", "=", notification_data.get("order_ref_1")),
                ("provider_code", "=", "sequra"),
            ]
        )
        if not tx:
            raise ValidationError(
                _(
                    "seQura: No transaction found matching reference %s.",
                    notification_data.get("ref"),
                )
            )
        return tx

    def _process_notification_data(self, notification_data):
        """Override of payment to process the transaction based on seQura data.

        Note: self.ensure_one()

        :param dict notification_data: The notification data sent by the provider
        :return: None
        """
        super()._process_notification_data(notification_data)
        if self.provider_code != "sequra":
            return
        reference = notification_data.get("order_ref_1")
        order = self.env["sale.order"].search([("name", "=", reference.split("-")[0])])
        if notification_data.get("signature") != self._sequra_generate_signature(order):
            _logger.info("Signature does not match")
            return
        payment_status = notification_data.get("sq_state")
        state = (payment_status == "approved" and "confirmed") or "on_hold"
        payload = self._sequra_prepare_payment_request_payload(reference, state=state)
        if not payload:
            return
        _logger.info("Send PUT to Update Order:\n%s", pprint.pformat(payload))
        update_order_response = self.provider_id._sequra_make_request(
            f'/orders/{notification_data.get("order_ref")}', data=payload, method="PUT"
        )
        if payment_status == "approved" and update_order_response.ok:
            self._set_done()
        elif payment_status == "needs_review" and update_order_response.ok:
            self._set_pending()
        elif not update_order_response.ok:
            _logger.info(
                "Could not update order with reference %s to status %s",
                self.reference,
                state,
            )
            self._set_error(
                _(
                    "seQura: Got %(code)s %(reason)s when updating the order."
                    " Body: %(body)s",
                    {
                        "code": update_order_response.status_code,
                        "reason": update_order_response.reason,
                        "body": update_order_response.text,
                    },
                )
            )
        else:
            _logger.info(
                "received data with invalid payment status (%s) "
                "for transaction with reference %s",
                payment_status,
                self.reference,
            )
            self._set_error(
                "seQura: "
                + _("Received data with invalid payment status: %s", payment_status)
            )
