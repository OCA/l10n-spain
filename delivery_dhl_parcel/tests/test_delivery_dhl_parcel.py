# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
from unittest import mock

from odoo.tests import Form, common

request_model = (
    "odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.DhlParcelRequest"
)

# There is also no public test user so we mock all API requests


class TestDeliveryDhlParcel(common.SingleTransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_dhl_parcel = cls.env["delivery.carrier"].create(
            {
                "name": "DHL Parcel",
                "delivery_type": "dhl_parcel",
                "product_id": cls.shipping_product.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "product", "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Odoo Ville",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.carrier_id = cls.carrier_dhl_parcel.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids[0]
        cls.picking.move_lines.quantity_done = 20

    @mock.patch("%s._get_new_auth_token" % request_model, return_value="12345")
    @mock.patch(
        "%s.create_shipment" % request_model,
        return_value={
            "Origin": "08",
            "Customer": "001000",
            "Tracking": "0870002260",
            "AWB": "",
            "LP": ["JJD00006080070002260001"],
            "Label": "JVBERiasdasdsdcfnsdhfbasdf==",
        },
    )
    def test_01_dhl_parcel_picking_confirm_success(self, redirect_mock, *args):
        self.picking.name = "ODOO-TEST-{}".format(time.time())
        self.picking.button_validate()
        self.assertEqual(
            self.picking.carrier_tracking_ref,
            "0870002260",
            "Tracking doesn't match test data",
        )

    @mock.patch("%s._get_new_auth_token" % request_model, return_value="12345")
    @mock.patch(
        "%s.track_shipment" % request_model,
        return_value=[
            {
                "DateTime": "2020-10-02T10:40:49",
                "Code": "A",
                "Status": "Es posible que la fecha prevista de entrega"
                " se posponga un día hábil",
                "Ubication": "Araba/Álava",
            }
        ],
    )
    def test_02_dhl_parcel_picking_update(self, redirect_mock, *args):
        self.picking.tracking_state_update()
        self.assertEqual(
            self.picking.tracking_state_history,
            (
                "2020-10-02T10:40:49 Araba/Álava - [A] Es posible que la fecha"
                " prevista de entrega se posponga un día hábil"
            ),
            "History doesn't match test data",
        )
        self.assertEqual(
            self.picking.tracking_state,
            (
                "[A] Es posible que la fecha"
                " prevista de entrega se posponga un día hábil"
            ),
            "State doesn't match test data",
        )
        self.assertEqual(
            self.picking.delivery_state,
            "shipping_recorded_in_carrier",
            "Delivery state doesn't match test data",
        )

    @mock.patch("%s._get_new_auth_token" % request_model, return_value="12345")
    @mock.patch("%s.hold_shipment" % request_model, return_value=True)
    @mock.patch("%s.release_shipment" % request_model, return_value=True)
    def test_03_dhl_parcel_picking_toggle_hold(self, redirect_mock, *args):
        self.assertFalse(self.picking.dhl_parcel_shipment_held)
        self.picking.dhl_parcel_toggle_hold_shipment()  # hold
        self.assertTrue(self.picking.dhl_parcel_shipment_held)
        self.picking.dhl_parcel_toggle_hold_shipment()  # release
        self.assertFalse(self.picking.dhl_parcel_shipment_held)

    @mock.patch("%s._get_new_auth_token" % request_model, return_value="12345")
    @mock.patch(
        "%s.end_day" % request_model,
        return_value={
            "Shipments": [
                {
                    "Origin": "08",
                    "Customer": "001000",
                    "Year": "1",
                    "Tracking": "0824005834",
                }
            ],
            "Report": "JVBERiasdasdsdcfnsdhfbasdf==",
        },
    )
    def test_04_dhl_parcel_endday(self, redirect_mock, *args):
        wizard = self.env["dhl.parcel.endday.wizard"].browse(
            self.carrier_dhl_parcel.action_open_end_day().get("res_id")
        )
        wizard.button_end_day()
        self.assertTrue(self.carrier_dhl_parcel.dhl_parcel_last_end_day_report)

    def test_05_dhl_parcel_get_tracking_link(self):
        tracking = self.carrier_dhl_parcel.get_tracking_link(self.picking)
        self.assertTrue(tracking)

    @mock.patch("%s._get_new_auth_token" % request_model, return_value="12345")
    @mock.patch(
        "%s.print_shipment" % request_model, return_value="JVBERiasdasdsdcfnsdhfbasdf=="
    )
    def test_06_dhl_parcel_get_label(self, redirect_mock, *args):
        label = self.picking.dhl_parcel_get_label()
        self.assertTrue(label)

    def test_07_dhl_parcel_rate_shipment(self):
        msg = self.carrier_dhl_parcel.dhl_parcel_rate_shipment(
            order=self.env["sale.order"]
        )
        self.assertIsInstance(msg, dict)

    @mock.patch("%s._get_new_auth_token" % request_model, return_value="12345")
    @mock.patch("%s.cancel_shipment" % request_model, return_value=True)
    def test_08_dhl_parcel_picking_cancel(self, redirect_mock, *args):
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.picking.cancel_shipment()
        self.picking.dhl_parcel_toggle_hold_shipment()
        self.picking.dhl_parcel_get_label()
        self.picking.tracking_state_update()
