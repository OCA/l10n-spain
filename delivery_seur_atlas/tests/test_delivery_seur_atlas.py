# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2024 Tecnativa - David Vidal
from unittest.mock import patch

from odoo.tests import Form, common
from odoo.tools import mute_logger

from odoo.addons.delivery_seur_atlas.models.seur_request_atlas import SeurAtlasRequest


def mock_set_token(self):
    self.token = "test"


class TestDeliverySeurAtlas(common.TransactionCase):
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
        return_value=[
            {"ecb": "47470138102387", "pack": "1/1", "label": "ZPL label..."}
        ],
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
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "028111000201420210716")
        self.picking.tracking_state_update()
        self.assertEqual(self.picking.delivery_state, "in_transit")
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
