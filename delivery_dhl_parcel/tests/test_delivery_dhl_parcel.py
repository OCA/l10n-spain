# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import time
from unittest import mock
from unittest.mock import MagicMock, Mock

from odoo.tests import Form, common

from odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request import DhlParcelRequest

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
                "dhl_parcel_cash_on_delivery": True,
            }
        )
        cls.carrier_other = cls.env["delivery.carrier"].create(
            {
                "name": "Other Carrier",
                "delivery_type": "fixed",
                "product_id": cls.shipping_product.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "name": "Test product"}
        )
        cls.parent_partner = cls.env["res.partner"].create(
            {
                "name": "Parent Company",
                "is_company": True,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Odoo Ville",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
                "street2": "Planta 1",
                "parent_id": cls.parent_partner.id,
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
        cls.picking.move_ids.quantity = 20
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "DHL Test",
                "delivery_type": "dhl_parcel",
                "dhl_parcel_uid": "test_user",
                "dhl_parcel_password": "test_pass",
                "dhl_parcel_label_format": "PDF",
                "product_id": cls.shipping_product.id,
            }
        )

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(
        f"{request_model}.create_shipment",
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
        self.picking.name = f"ODOO-TEST-{time.time()}"
        self.picking.button_validate()
        self.assertEqual(
            self.picking.carrier_tracking_ref,
            "0870002260",
            "Tracking doesn't match test data",
        )

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_get_new_auth_token_success(self, mock_requests):
        mock_response = Mock()
        mock_response.json.return_value = "fake_token_123"
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response
        dhl = DhlParcelRequest(self.carrier)
        self.assertEqual(dhl.token, "fake_token_123")
        mock_requests.post.assert_called_once_with(
            url="https://external.dhl.es/cimapi/api/v1/customer/authenticate",
            json={"Username": "test_user", "Password": "test_pass"},
            headers={},
            timeout=60,
        )

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_create_shipment(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)
            dhl.year = "5"
        mock_response = Mock()
        mock_response.json.return_value = {
            "Tracking": "1234567890",
            "Label": "base64data...",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response
        vals = {"Reference": "SO123", "Weight": 1.5}
        result = dhl.create_shipment(vals)

        self.assertEqual(result["Tracking"], "1234567890")
        mock_requests.post.assert_called_once_with(
            url="https://external.dhl.es/cimapi/api/v1/customer/shipment",
            json=vals,
            headers={"Authorization": "Bearer valid_token"},
            timeout=60,
        )

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_track_shipment(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)

        mock_response = Mock()
        mock_response.json.return_value = {
            "Tracking": "1234567890",
            "Events": [{"Code": "A", "Status": "Assigned"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        result = dhl.track_shipment(reference="1234567890", track="status")
        self.assertEqual(result["Tracking"], "1234567890")
        self.assertIn("Events", result)

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_print_shipment(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)
            dhl.year = "5"

        mock_response = Mock()
        mock_response.json.return_value = {"Label": "base64_label_data"}
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        label = dhl.print_shipment(reference="1234567890")
        self.assertEqual(label, "base64_label_data")

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_cancel_shipment(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)
            dhl.year = "5"

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_requests.get.return_value = mock_response

        res = dhl.cancel_shipment(reference="1234567890")
        self.assertEqual(res, mock_response)

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_hold_shipment_success(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)
            dhl.year = "5"

        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response

        result = dhl.hold_shipment(reference="1234567890")
        self.assertTrue(result)

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_end_day(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)

        mock_response = Mock()
        mock_response.json.return_value = {
            "Shipments": [{"Tracking": "1234567890"}],
            "Report": "base64_report",
        }
        mock_response.raise_for_status.return_value = None
        mock_requests.post.return_value = mock_response

        result = dhl.end_day(customers="ALL", report_type="PDF")
        self.assertIn("Report", result)
        self.assertEqual(result["Report"], "base64_report")

    @mock.patch("odoo.addons.delivery_dhl_parcel.models.dhl_parcel_request.requests")
    def test_release_shipment_success(self, mock_requests):
        with mock.patch.object(
            DhlParcelRequest, "_get_new_auth_token", return_value="valid_token"
        ):
            dhl = DhlParcelRequest(self.carrier)
            dhl.year = "5"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_requests.get.return_value = mock_response
        result = dhl.release_shipment(reference="1234567890")
        self.assertTrue(result)
        expected_url = (
            "https://external.dhl.es/cimapi/api/v1/customer/"
            "shipment?Year=5&Tracking=1234567890&Action=RELEASE"
        )
        mock_requests.get.assert_called_once_with(
            url=expected_url,
            headers={"Authorization": "Bearer valid_token"},
            timeout=60,
        )

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(
        f"{request_model}.track_shipment",
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

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(f"{request_model}.hold_shipment", return_value=True)
    @mock.patch(f"{request_model}.release_shipment", return_value=True)
    def test_03_dhl_parcel_picking_toggle_hold(self, redirect_mock, *args):
        self.assertFalse(self.picking.dhl_parcel_shipment_held)
        self.picking.dhl_parcel_toggle_hold_shipment()  # hold
        self.assertTrue(self.picking.dhl_parcel_shipment_held)
        self.picking.dhl_parcel_toggle_hold_shipment()  # release
        self.assertFalse(self.picking.dhl_parcel_shipment_held)

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(
        f"{request_model}.end_day",
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

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(
        f"{request_model}.print_shipment", return_value="JVBERiasdasdsdcfnsdhfbasdf=="
    )
    def test_06_dhl_parcel_get_label(self, redirect_mock, *args):
        label = self.picking.dhl_parcel_get_label()
        self.assertTrue(label)

    def test_07_dhl_parcel_rate_shipment(self):
        msg = self.carrier_dhl_parcel.dhl_parcel_rate_shipment(
            order=self.env["sale.order"]
        )
        self.assertIsInstance(msg, dict)

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(f"{request_model}.cancel_shipment")
    def test_08_dhl_parcel_picking_cancel(self, mock_cancel, *args):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Message": "Invalid tracking"}
        mock_cancel.return_value = mock_response
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.picking.cancel_shipment()
        self.picking.dhl_parcel_toggle_hold_shipment()
        self.picking.dhl_parcel_get_label()
        self.picking.tracking_state_update()

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(f"{request_model}.cancel_shipment")
    def test_08_dhl_parcel_cancel_whit_shipment_held(self, mock_cancel, *args):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_cancel.return_value = mock_response
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.picking.dhl_parcel_shipment_held = True
        self.picking.cancel_shipment()
        self.picking.dhl_parcel_toggle_hold_shipment()
        self.picking.dhl_parcel_get_label()
        self.picking.tracking_state_update()

    def test_09_dhl_carrier_can_return(self):
        self.assertTrue(self.carrier_dhl_parcel.can_generate_return)
        self.assertFalse(self.carrier_other.can_generate_return)

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(f"{request_model}.cancel_shipment")
    def test_10_dhl_parcel_cancel_shipment_no_response(self, mock_cancel, *args):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"Message": "Invalid tracking"}
        mock_cancel.return_value = mock_response
        self.picking.carrier_tracking_ref = "1234567890"
        self.carrier_dhl_parcel.dhl_parcel_cancel_shipment(self.picking)
        self.assertIn(
            "DHL Parcel Cancellation failed with reason:",
            self.picking.message_ids[0].body,
        )
        self.picking.cancel_shipment()
        self.picking.dhl_parcel_toggle_hold_shipment()
        self.picking.dhl_parcel_get_label()

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    @mock.patch(
        f"{request_model}.create_shipment",
        return_value={},
    )
    def test_11_send_shipping_fail_response(self, redirect_mock, *args):
        values = self.carrier_dhl_parcel.dhl_parcel_send_shipping(self.picking)
        self.assertTrue(values)

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    def test_12_dhl_parcel_hold_no_tracking_ref(self, mock):
        res = self.carrier.dhl_parcel_hold_shipment(False)
        self.assertFalse(res)

    @mock.patch(f"{request_model}._get_new_auth_token", return_value="12345")
    def test_13_dhl_parcel_held_no_tracking_ref(self, mock):
        res = self.carrier.dhl_parcel_release_shipment(False)
        self.assertFalse(res)
