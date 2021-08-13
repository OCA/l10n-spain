# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import base64

from odoo import _, fields, models

from .dbschenker_request import (
    DBSCHENKER_CONSIGNEE_DATE_TYPE,
    DBSCHENKER_CONTAINER_TYPE,
    DBSCHENKER_MEASURE_UNIT,
    DBSCHENKER_PACKAGE_TYPE,
    DBSCHENKER_PRECARRIAGE_TYPE,
)


class StockPicking(models.Model):
    _inherit = "stock.picking"

    dbschenker_request_type = fields.Selection(
        string="Request type", related="carrier_id.dbschenker_request_type"
    )
    dbschenker_service_type = fields.Selection(
        string="Service type", related="carrier_id.dbschenker_service_type"
    )
    dbschenker_incoterm_id = fields.Many2one(
        comodel_name="account.incoterms", string="Incoterms"
    )
    dbschenker_incoterm_location = fields.Char(string="Incoterm location")
    # Land, Air, OceanLCL
    dbschenker_package_type = fields.Selection(
        string="Package type", selection=DBSCHENKER_PACKAGE_TYPE
    )
    dbschenker_volume = fields.Float(string="Volume")
    dbschenker_cargo_desc = fields.Char(string="Cargo description")
    dbschenker_stackable = fields.Boolean(string="Stackable")
    # Air
    dbschenker_departure_airport = fields.Char(
        string="Departure airport",
        help="Defines 3-character IATA airport code of destination",
    )
    dbschenker_destination_airport = fields.Char(
        string="Destination airport",
        help="Defines 3-character IATA airport code of destination",
    )
    dbschenker_precarriage_type = fields.Selection(
        string="Precarriage type", selection=DBSCHENKER_PRECARRIAGE_TYPE
    )
    # OceanFCL
    dbschenker_container_type = fields.Selection(
        string="Container type", selection=DBSCHENKER_CONTAINER_TYPE
    )
    dbschenker_container_number = fields.Char(string="Container number")
    dbschenker_loading_port = fields.Char(
        string="Loading port", help="Needs to be UN LOCODE format"
    )
    dbschenker_discharge_port = fields.Char(
        string="Discharge port", help="Needs to be UN LOCODE format"
    )
    # Land
    dbschenker_measure_unit = fields.Selection(
        string="Unit of measure", selection=DBSCHENKER_MEASURE_UNIT, default="PIECES"
    )
    dbschenker_measure_value = fields.Float(string="Value")
    dbschenker_express = fields.Boolean(string="Express shipment")
    dbschenker_food = fields.Boolean(string="Food related shipment")
    dbschenker_heated = fields.Boolean(string="Heated transport required")
    dbschenker_home_delivery = fields.Boolean(string="Home delivery required")
    dbschenker_own_pickup = fields.Boolean(string="Own pickup required")
    dbschenker_pharmaceuticals = fields.Boolean(string="Pharmaceutical shipment")
    dbschenker_show_consignee_date_info = fields.Boolean(
        string="Show consignee delivery date info"
    )
    dbschenker_consignee_date_type = fields.Selection(
        string="Consignee delivery date type", selection=DBSCHENKER_CONSIGNEE_DATE_TYPE
    )
    dbschenker_consignee_date = fields.Datetime(string="Consignee delivery date")
    dbschenker_time_from = fields.Char(string="Time from", help="00:00-23:59")
    dbschenker_time_to = fields.Char(string="Time to", help="00:00-23:59")

    def dbschenker_get_label(self):
        """Get DB Schenker Label for this picking expedition"""
        self.ensure_one()
        tracking_ref = self.carrier_tracking_ref
        if self.delivery_type != "dbschenker" or not tracking_ref:
            return
        label = base64.b64decode(self.carrier_id._dbschenker_get_label(tracking_ref))
        label_name = "db_schenker_{}.pdf".format(tracking_ref)
        self.message_post(
            body=(_("DB Schenker label for %s") % tracking_ref),
            attachments=[(label_name, label)],
        )
        return label
