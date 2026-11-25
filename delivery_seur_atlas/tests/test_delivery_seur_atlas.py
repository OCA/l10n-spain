# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2024 Tecnativa - David Vidal
import base64
import json
from unittest import mock
from unittest.mock import patch

from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.delivery_seur_atlas.models.seur_request_atlas import SeurAtlasRequest


def mock_set_token(self):
    self.token = "test"


class TestDeliverySeurAtlas(BaseCommon):
    _test_user_groups = (
        "stock.group_stock_manager",
        "base.group_partner_manager",
    )

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        # TODO: Try to get persistent real test credentials
        cls.carrier_seur_atlas = cls.env["delivery.carrier"].create(
            {
                "name": "Seur Atlas",
                "delivery_type": "seur_atlas",
                "product_id": cls.shipping_product.id,
                "debug_logging": True,
                "prod_environment": False,
                "seur_atlas_account_code": "01234-01234",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "name": "Test product"}
        )
        cls.wh_partner = cls.env["res.partner"].create(
            {
                "name": "My Spanish WH",
                "city": "Zaragoza",
                "zip": "50001",
                "street": "C/ Mayor, 1",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co. [ñáéíóú]",
                "city": "Madrid",
                "zip": "28001",
                "email": "odoo@test.com",
                "street": "Calle de La Rua, 3",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_seur_atlas
        cls.sale_order.action_confirm()
        # Ensure shipper address
        cls.sale_order.warehouse_id.partner_id = cls.wh_partner
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_ids.quantity = 20

    @mute_logger("odoo.sql_db")
    @patch.object(SeurAtlasRequest, "_set_token", mock_set_token)
    @patch.object(
        SeurAtlasRequest,
        "shipments",
        return_value={
            "shipmentCode": "028111000201420210716",
            "ecbs": ["28280126971198"],
            "parcelNumbers": ["07280434535625"],
        },
    )
    @patch.object(
        SeurAtlasRequest,
        "labels",
        return_value=[{"ecb": "47470138102387", "pack": "1/1", "label": "ZPL label ñ"}],
    )
    @patch.object(
        SeurAtlasRequest,
        "tracking_services__extended",
        return_value=[
            {
                "eventCode": "LI407",
                "description": "EN CAMINO",
                "situationDate": "2021-01-21T00:00:00.000",
            }
        ],
    )
    @patch.object(
        SeurAtlasRequest,
        "shipments__cancel",
        return_value=[
            {
                "shipmentCode": "028111000201420210716",
                "description": "The shipment has been cancelled correctly",
            }
        ],
    )
    def test_01_seur_atlas_picking_confirm_simple(
        self, patch_shipments, patch_labels, patch_tracking, patch_cancel
    ):
        """The picking is confirm and the shipping is recorded into Seur"""
        # TODO: Try to get persistent credentials to avoid mocks
        self.carrier_seur_atlas.seur_atlas_label_format = "ZPL"
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "028111000201420210716")
        # The ZPL label is attached to the picking, encoded as SEUR sends it
        label = self.env["ir.attachment"].search(
            [("res_model", "=", "stock.picking"), ("res_id", "=", self.picking.id)]
        )
        self.assertEqual(label.name, "seur_47470138102387.txt")
        self.assertEqual(label.mimetype, "text/plain")
        self.assertEqual(label.raw.content, "ZPL label ñ".encode("iso-8859-15"))
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.delivery_state, "in_transit")
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)

    def _mock_seur_api(self, data_by_endpoint):
        """Patch the HTTP calls to the SEUR Atlas API: the token request and
        each API endpoint, which answers ``{"data": data_by_endpoint[endpoint]}``.
        Returns the list of (method, endpoint, request kwargs) sent."""
        calls = []

        def response(content):
            res = mock.MagicMock(ok=True, status_code=200, text=json.dumps(content))
            res.content = res.text.encode()
            res.json.return_value = content
            return res

        def request(method, url, **kwargs):
            endpoint = url.split("/pic/v1/")[1]
            calls.append((method, endpoint, kwargs))
            return response({"data": data_by_endpoint[endpoint]})

        module = "odoo.addons.delivery_seur_atlas.models.seur_request_atlas.requests"
        self.startPatcher(
            patch(f"{module}.post", return_value=response({"access_token": "tk"}))
        )
        self.startPatcher(patch(f"{module}.request", side_effect=request))
        return calls

    def test_02_seur_atlas_pdf_label(self):
        """A PDF label arrives in base64 and is attached as a printable PDF"""
        calls = self._mock_seur_api(
            {
                "shipments": {"shipmentCode": "028111000201420210717"},
                "labels": [
                    {
                        "ecb": "47470138102388",
                        "pack": "1/1",
                        "pdf": base64.b64encode(b"%PDF-1.4 label").decode(),
                    }
                ],
            }
        )
        self.carrier_seur_atlas.seur_atlas_label_format = "PDF"
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "028111000201420210717")
        self.assertEqual([c[1] for c in calls], ["shipments", "labels"])
        self.assertEqual(calls[1][2]["params"]["type"], "PDF")
        label = self.env["ir.attachment"].search(
            [("res_model", "=", "stock.picking"), ("res_id", "=", self.picking.id)]
        )
        self.assertEqual(label.name, "seur_47470138102388.pdf")
        self.assertEqual(label.mimetype, "application/pdf")
        self.assertEqual(label.raw.content, b"%PDF-1.4 label")

    def test_03_seur_atlas_tracking_incident(self):
        """SEUR incidences and unknown events set the incident carrier state"""
        self._mock_seur_api(
            {
                "shipments": {"shipmentCode": "028111000201420210718"},
                "labels": [
                    {
                        "ecb": "47470138102389",
                        "pack": "1/1",
                        "pdf": base64.b64encode(b"%PDF-1.4 label").decode(),
                    }
                ],
                "tracking-services/extended": [
                    {
                        "situations": [
                            {
                                "situationDate": "2026-11-20T09:15:00",
                                "eventCode": "LI527",
                                "description": "NO CONTESTA TELEFONO",
                            }
                        ]
                    }
                ],
            }
        )
        self.picking.button_validate()
        self.picking.tracking_state_update()
        self.assertIn("[LI527] NO CONTESTA TELEFONO", self.picking.tracking_state)
        self.assertEqual(self.picking.delivery_state, "incident")

    def test_04_seur_atlas_shipping_comments(self):
        """The picking note reaches SEUR as plain text"""
        calls = self._mock_seur_api(
            {
                "shipments": {"shipmentCode": "028111000201420210719"},
                "labels": [
                    {
                        "ecb": "47470138102390",
                        "pack": "1/1",
                        "pdf": base64.b64encode(b"%PDF-1.4 label").decode(),
                    }
                ],
            }
        )
        self.picking.note = "<p>Ring twice</p>"
        self.picking.button_validate()
        self.assertEqual(calls[0][2]["json"]["comments"], "Ring twice")
