# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64
from datetime import datetime

from odoo import _, fields, models

from .dbschenker_request import (
    DBSCHENKER_PRODUCT_CODES,
    DBSCHENKER_REQUEST_TYPES,
    DBSCHENKER_SERVICE_TYPES,
    DBSchenkerRequest,
)


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    delivery_type = fields.Selection(
        selection_add=[("dbschenker", "DB Schenker")],
        ondelete={"dbschenker": "set default"},
    )
    dbschenker_accesskey = fields.Char(string="Access Key")
    dbschenker_request = fields.Char(string="Request ID")
    dbschenker_user = fields.Char(string="User ID")
    dbschenker_group = fields.Char(string="Group ID")
    dbschenker_groupname = fields.Char(string="Group Name")
    dbschenker_request_label = fields.Boolean(string="Request label with booking")
    dbschenker_label_size = fields.Selection(
        string="Label size", selection=[("A4", "A4"), ("A6", "A6")]
    )
    dbschenker_request_type = fields.Selection(
        string="Request type", selection=DBSCHENKER_REQUEST_TYPES
    )
    dbschenker_product_code = fields.Selection(
        string="Product code", selection=DBSCHENKER_PRODUCT_CODES
    )
    dbschenker_service_type = fields.Selection(
        string="Service type", selection=DBSCHENKER_SERVICE_TYPES
    )
    dbschenker_measurement = fields.Selection(
        string="Measurement", selection=[("METRIC", "Metric"), ("IMPERIAL", "Imperial")]
    )
    dbschenker_customs_clearance = fields.Boolean(
        string="Is customs clearance required?"
    )
    dbschenker_indoors_delivery = fields.Boolean(string="Is indoors delivery required?")

    def dbschenker_get_tracking_link(self, picking):
        """Provide tracking link for the customer"""
        tracking_url = (
            "https://eschenker.dbschenker.com/app/tracking-public/schenker-search"
            "?refNumber={}&language_region=es-ES_ES"
        )
        return tracking_url.format(picking.carrier_tracking_ref)

    def _prepare_dbschenker_applicationarea_vals(self):
        return {
            "access_key": self.dbschenker_accesskey,  # Mandatory
            "request_id": self.dbschenker_request or "",
            "user_id": self.dbschenker_user or "",
            "group_id": self.dbschenker_group or "",
            "group_name": self.dbschenker_groupname or "",
        }

    def _prepare_dbschenker_address_vals(self, picking):
        """Convert picking values for DB Schenker
        :param picking record with picking to send
        :returns dict values for the connector
        """
        self.ensure_one()
        shipper = (
            picking.picking_type_id.warehouse_id.partner_id
            or picking.company_id.partner_id
        )
        consignee = picking.partner_id
        return [
            {
                "email": shipper.email or shipper.parent_id.email or "",
                "name": shipper.name or shipper.parent_id.name or "",  # Mandatory
                "name2": "",
                "cust_address": "",
                "fax": "",
                "industry": "",
                "location": "PHYSICAL",
                "mobile": shipper.mobile or shipper.parent_id.mobile or "",
                "person_type": "COMPANY" if shipper.is_company else "PERSON",
                "phone": shipper.phone or shipper.parent_id.phone or "",
                "po_box": "",
                "postal_code": shipper.zip or shipper.parent_id.zip or "",  # Mandatory
                "state_code": "",
                "lang": "ES",
                "street": shipper.street or shipper.parent_id.street or "",  # Mandatory
                "street2": shipper.street2 or shipper.parent_id.street2 or "",
                "city": shipper.city or shipper.parent_id.city or "",  # Mandatory
                "country": (
                    shipper.country_id.code or shipper.parent_id.country_id.code
                ),  # Mandatory
                "type": "SHIPPER",  # Mandatory
            },
            {
                "email": consignee.email or consignee.parent_id.email or "",
                "name": consignee.name or consignee.parent_id.name or "",  # Mandatory
                "name2": "",
                "cust_address": "",
                "fax": "",
                "industry": "",
                "location": "PHYSICAL",
                "mobile": consignee.mobile or consignee.parent_id.mobile or "",
                "person_type": "COMPANY" if consignee.is_company else "PERSON",
                "phone": consignee.phone or consignee.parent_id.phone or "",
                "po_box": "",
                "postal_code": (
                    consignee.zip or consignee.parent_id.zip or ""
                ),  # Mandatory
                "state_code": "",
                "lang": "ES",
                "street": (
                    consignee.street or consignee.parent_id.street or ""
                ),  # Mandatory
                "street2": consignee.street2 or consignee.parent_id.street2 or "",
                "city": consignee.city or consignee.parent_id.city or "",  # Mandatory
                "country": (
                    consignee.country_id.code or consignee.parent_id.country_id.code
                ),  # Mandatory
                "type": "CONSIGNEE",  # Mandatory
            },
        ]

    def _prepare_dbschenker_pickup_date_vals(self, picking):
        def _to_timezone_date(date):
            return datetime.strftime(date, "%Y-%m-%dT%H:%M:%S+02:00")

        return [
            {
                "date_from": _to_timezone_date(datetime.now()),  # Mandatory
                "date_to": _to_timezone_date(datetime.now()),  # Mandatory
            }
        ]

    def _prepare_dbschenker_reference_vals(self, picking):
        return [{"number": picking.name or "", "id": "SHIPPER_REFERENCE_NUMBER"}]

    def _prepare_dbschenker_shipping_position_vals(self, picking):
        return {
            "dgr": "false",  # Mandatory
            "cargo_description": picking.dbschenker_cargo_desc or "",  # Mandatory
            "shipping_length": "",
            "shipping_width": "",
            "shipping_height": "",
            "shipping_volume": picking.dbschenker_volume,  # Mandatory
            "shipping_gross_weight": round(picking.shipping_weight, 2),  # Mandatory
            "shipping_package_type": picking.dbschenker_package_type or "",  # Mandatory
            "shipping_pieces": picking.number_of_packages or 1,  # Mandatory
            "shipping_stackable": str(
                picking.dbschenker_stackable
            ).lower(),  # Mandatory
        }

    def _prepare_dbschenker_consignee_date_vals(self, picking):
        vals = {}
        if picking.dbschenker_show_consignee_date_info:
            vals.update(
                {
                    "date_type": picking.dbschenker_consignee_date_type,  # Mandatory
                    "delivery_date": datetime.strftime(
                        picking.dbschenker_consignee_date, "%Y-%m-%dT%H:%M:%S+02:00"
                    ),  # Mandatory
                    "time_from": picking.dbschenker_time_from,  # if date_type = TIME
                    "time_to": picking.dbschenker_time_to,  # if date_type = TIME
                }
            )
        return vals

    def _prepare_dbschenker_land_vals(self, picking):
        return {
            "shipping_position_vals": self._prepare_dbschenker_shipping_position_vals(
                picking
            ),  # Mandatory
            "consignee_date_vals": self._prepare_dbschenker_consignee_date_vals(
                picking
            ),
            "volume": picking.dbschenker_volume,  # Mandatory
            "weight": round(picking.shipping_weight, 2),  # Mandatory
            "express": str(picking.dbschenker_express).lower(),  # Mandatory
            "food": str(picking.dbschenker_food).lower(),  # Mandatory
            "heated_transport": str(picking.dbschenker_heated).lower(),  # Mandatory
            "home_delivery": str(picking.dbschenker_home_delivery).lower(),  # Mandatory
            "measure_unit": picking.dbschenker_measure_unit,  # Mandatory
            "measure_value": (
                picking.number_of_packages
                if picking.dbschenker_measure_unit == "PIECES"
                else picking.dbschenker_measure_value
            ),  # Mandatory
            "own_pickup": str(picking.dbschenker_own_pickup).lower(),  # Mandatory
            "pharmaceuticals": str(
                picking.dbschenker_pharmaceuticals
            ).lower(),  # Mandatory
        }

    def _prepare_dbschenker_air_vals(self, picking):
        return {
            "shipping_position_vals": self._prepare_dbschenker_shipping_position_vals(
                picking
            ),  # Mandatory
            "volume": picking.dbschenker_volume,  # Mandatory
            "weight": round(picking.shipping_weight, 2),  # Mandatory
            "air_business": "",
            "departure_airport": (
                picking.dbschenker_departure_airport or ""
            ),  # Mandatory if A2D/A2A
            "destination_airport": (
                picking.dbschenker_destination_airport or ""
            ),  # Mandatory if D2A/A2A
            "precarriage_type": (
                picking.dbschenker_precarriage_type or ""
            ),  # Mandatory
        }

    def _prepare_dbschenker_oceanfcl_vals(self, picking):
        return {
            "ocean_business": "",
            "loading_port": (
                picking.dbschenker_loading_port or ""
            ),  # Mandatory if P2D/P2P
            "discharge_port": (
                picking.dbschenker_discharge_port or ""
            ),  # Mandatory if D2P/P2P
            "container_vals": {
                "container_type": (
                    picking.dbschenker_container_type or ""
                ),  # Mandatory
                "container_number": picking.dbschenker_container_number or "",
                "positioning_date": "",
                "positioning_address": "",
                "seal_number": "",
            },
        }

    def _prepare_dbschenker_oceanlcl_vals(self, picking):
        return {
            "shipping_position_vals": self._prepare_dbschenker_shipping_position_vals(
                picking
            ),  # Mandatory
            "volume": picking.dbschenker_volume or "",  # Mandatory
            "weight": round(picking.shipping_weight, 2),  # Mandatory
            "ocean_business": "",
            "loading_port": (
                picking.dbschenker_loading_port or ""
            ),  # Mandatory if P2D/P2P
            "discharge_port": (
                picking.dbschenker_discharge_port or ""
            ),  # Mandatory if D2P/P2P
            "precarriage_type": (
                picking.dbschenker_precarriage_type or ""
            ),  # Mandatory
        }

    def _prepare_dbschenker_type_fields_vals(self, picking):
        booking_type = self.dbschenker_request_type
        if booking_type == "Land":
            return self._prepare_dbschenker_land_vals(picking)
        elif booking_type == "Air":
            return self._prepare_dbschenker_air_vals(picking)
        elif booking_type == "OceanFCL":
            return self._prepare_dbschenker_oceanfcl_vals(picking)
        elif booking_type == "OceanLCL":
            return self._prepare_dbschenker_oceanlcl_vals(picking)
        raise NotImplementedError(
            _("Booking requests of type {} are not implemented.", booking_type)
        )

    def _prepare_booking_vals(self, picking):
        return {
            "type": self.dbschenker_request_type,  # Mandatory
            "barcode_size": (
                self.dbschenker_label_size if self.dbschenker_request_label else ""
            ),
            "incoterm": picking.dbschenker_incoterm_id.code,  # Mandatory
            "incoterm_location": picking.dbschenker_incoterm_location,  # Mandatory
            "product_code": self.dbschenker_product_code,  # Mandatory
            "measurement": self.dbschenker_measurement,  # Mandatory
            "cargo_description": picking.note,
            "customs_clearance": str(
                self.dbschenker_customs_clearance
            ).lower(),  # Mandatory
            "weight": round(picking.shipping_weight, 2),  # Mandatory,
            "indoor_delivery": str(
                self.dbschenker_indoors_delivery
            ).lower(),  # Mandatory
            "handling": "",
            "neutral_shipping": "false",  # Mandatory
            "special_cargo": "false",  # Mandatory
            "special_cargo_desc": "",
            "value": "",
            "currency": "",
            "waybill_number": "",
            "incoterm_dest": "",
            "service": self.dbschenker_service_type or "",  # Mandatory
            "picking": picking,
            "applicationarea_vals": (
                self._prepare_dbschenker_applicationarea_vals()
            ),  # Mandatory
            "address_vals": self._prepare_dbschenker_address_vals(picking),  # Mandatory
            "pickup_date_vals": self._prepare_dbschenker_pickup_date_vals(
                picking
            ),  # Mandatory
            "reference_vals": self._prepare_dbschenker_reference_vals(picking),
            "type_fields": self._prepare_dbschenker_type_fields_vals(
                picking
            ),  # Mandatory
        }

    def _prepare_dbschenker_label_vals(self, carrier_tracking_ref):
        return {
            "applicationarea_vals": self._prepare_dbschenker_applicationarea_vals(),
            "reference": carrier_tracking_ref,
            "format": self.dbschenker_label_size,
        }

    def _prepare_dbschenker_cancel_vals(self, carrier_tracking_ref):
        return {
            "applicationarea_vals": self._prepare_dbschenker_applicationarea_vals(),
            "booking_id": carrier_tracking_ref,
        }

    def dbschenker_send_shipping(self, pickings):
        """Send the package to DB Schenker
        :param pickings: A recordset of pickings
        :return list: A list of dictionaries although in practice it's
        called one by one and only the first item in the dict is taken. Due
        to this design, we have to inject vals in the context to be able to
        add them to the message.
        """
        request = DBSchenkerRequest(self)
        result = []
        for picking in pickings:
            vals = self._prepare_booking_vals(picking)
            response = request._send_shipping(vals)
            if not response:
                result.append(vals)
                continue
            vals.update(
                {"tracking_number": response.get("bookingId", ""), "exact_price": 0}
            )
            attachment = []
            if response.get("barcodeDocument"):
                attachment = [
                    (
                        "dbschenker_{}.pdf".format(response.get("bookingId", "")),
                        base64.b64decode(response.get("barcodeDocument")),
                    )
                ]
            picking.message_post(body=_(""), attachments=attachment)
            result.append(vals)
        return result

    def dbschenker_tracking_state_update(self, picking):
        """Tracking state update"""
        self.ensure_one()
        if not picking.carrier_tracking_ref:
            return
        raise NotImplementedError(
            _(
                """
                Tracking states not implemented for DB Schenker currently
            """
            )
        )

    def dbschenker_cancel_shipment(self, pickings):
        """Cancel the expedition"""
        dbschenker_request = DBSchenkerRequest(self)
        for picking in pickings.filtered("carrier_tracking_ref"):
            response = dbschenker_request._cancel_shipping(
                self._prepare_dbschenker_cancel_vals(picking.carrier_tracking_ref)
            )
            if not response:
                msg = _(
                    "DB Schenker cancellation failed with reason: %s"
                ) % response.get("error", "Connection Error")
                picking.message_post(body=msg)
                continue
            picking.carrier_tracking_ref = False
            picking.message_post(
                body=_("DB Schenker booking with id %s cancelled")
                % picking.carrier_tracking_ref
            )

    def _dbschenker_get_label(self, carrier_tracking_ref):
        """Generate label for picking
        :param str carrier_tracking_ref - tracking reference
        :returns base64 encoded label
        """
        self.ensure_one()
        if not carrier_tracking_ref:
            return False
        dbschenker_request = DBSchenkerRequest(self)
        label = dbschenker_request._print_shipment_label(
            self._prepare_dbschenker_label_vals(carrier_tracking_ref)
        )
        return label or False

    def dbschenker_rate_shipment(self, order):
        """Not implemented"""
        raise NotImplementedError(
            _(
                """
                DB Schenker API doesn't provide methods to compute delivery rates, so
                you should rely on another price method instead or override this
                one in your custom code.
            """
            )
        )
