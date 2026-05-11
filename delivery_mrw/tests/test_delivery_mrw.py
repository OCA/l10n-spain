import datetime
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon
from odoo.addons.delivery_mrw.models.mrw_request import MRWRequest


class TestDeliveryMRW(BaseCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        spain = cls.env["res.country"].search([("code", "=", "ES")])
        cls.env.company.partner_id.country_id = spain
        cls.env.company.external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_mrw = cls.env.ref("delivery_mrw.mrw_carrier_test")
        cls.carrier_mrw.write(
            {
                "product_id": cls.shipping_product.id,
                "company_id": cls.env.company.id,
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "consu", "is_storable": True, "name": "Test product"}
        )
        stock_location = cls.env.ref("stock.stock_location_stock")
        inventory = cls.env["stock.quant"].create(
            {
                "product_id": cls.product.id,
                "location_id": stock_location.id,
                "inventory_quantity": 100,
            }
        )
        inventory.action_apply_inventory()
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Madrid",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
                "street2": "4-1",
                "country_id": spain.id,
                "phone": "777777777",
            }
        )
        order_form = Form(cls.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.date_order = datetime.datetime.today()
        cls.sale_order.carrier_id = cls.carrier_mrw.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        assert cls.product.qty_available == 100

    @mock.patch("odoo.addons.delivery_mrw.models.mrw_request.Client")
    @mock.patch(
        "odoo.addons.delivery_mrw.models.delivery_carrier.DeliveryCarrier.mrw_get_label",
        return_value={
            "EtiquetaFile": b"%PDF-1.4 fake PDF content",
        },
    )
    def test_01_mrw_manifest(self, mock, *arg):
        """Manifest is created without calling real MRW API"""
        self.picking.name = "picking1"
        self.picking.number_of_packages = 1
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_ids.quantity = self.picking.move_ids.product_uom_qty
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertTrue(self.picking.carrier_tracking_ref)
        wizard = self.env["mrw.manifest.wizard"].create(
            {"carrier_id": self.carrier_mrw.id, "date_from": datetime.date.today()}
        )
        manifest_data = wizard.get_manifest()["data"]["deliveries"]
        self.assertEqual(
            manifest_data[-1]["carrier_tracking_ref"], self.picking.carrier_tracking_ref
        )

    def test_02_mrw_get_tracking_link_national(self):
        self.picking.carrier_tracking_ref = "MRW123456789"
        self.carrier_mrw.international_shipping = False
        national_link = self.carrier_mrw.mrw_get_tracking_link(self.picking)
        self.assertIn("modo=nacional", national_link)
        self.assertIn("envio=MRW123456789", national_link)

    def test_03_get_notifications(self):
        self.partner.email = "test@example.com"

        self.carrier_mrw.write(
            {"mrw_notification_channel": "1", "mrw_notification_type": "2"}
        )
        email_notifications = self.carrier_mrw.get_notifications(self.partner)
        self.assertEqual(
            email_notifications["NotificacionRequest"]["CanalNotificacion"], "1"
        )
        self.assertEqual(
            email_notifications["NotificacionRequest"]["MailSMS"], "test@example.com"
        )

        self.carrier_mrw.write(
            {"mrw_notification_channel": "2", "mrw_notification_type": "5"}
        )
        sms_notifications = self.carrier_mrw.get_notifications(self.partner)
        self.assertEqual(
            sms_notifications["NotificacionRequest"]["CanalNotificacion"], "2"
        )

        self.carrier_mrw.mrw_notification_channel = False
        self.assertEqual(self.carrier_mrw.get_notifications(self.partner), {})

    def test_04_mrw_address_without_street_raises(self):
        partner_no_street = self.partner.copy(
            {
                "name": "No Street Partner",
                "street": False,
                "street2": False,
            }
        )
        with self.assertRaises(UserError):
            self.carrier_mrw.mrw_address(partner_no_street, international=False)

    def test_05_manifest_no_deliveries_raises(self):
        wizard = self.env["mrw.manifest.wizard"].create(
            {
                "carrier_id": self.carrier_mrw.id,
                "date_from": datetime.date(1999, 1, 1),
            }
        )
        with self.assertRaises(UserError):
            wizard.get_manifest()

    def test_06_stock_picking_get_label_returns_empty_without_tracking(self):
        self.picking.carrier_tracking_ref = False
        self.assertFalse(self.picking.mrw_get_label())

    def test_07_mrw_check_response(self):
        with self.assertRaises(UserError):
            self.carrier_mrw._mrw_check_response({"Estado": "0", "Mensaje": "error"})

        self.assertEqual(
            self.carrier_mrw._mrw_check_response(
                {"Estado": "1", "Mensaje": "ok message"}
            ),
            "ok message",
        )
        self.assertEqual(
            self.carrier_mrw._mrw_check_response({"Estado": "1", "Mensaje": ""}),
            "",
        )

    def test_08_prepare_mrw_shipping_national(self):
        self.carrier_mrw.write(
            {
                "international_shipping": False,
                "mrw_horario_from": 9.0,
                "mrw_horario_to": 14.0,
                "mrw_national_service": "0005",
                "mrw_reembolso": "D",
            }
        )
        self.picking.number_of_packages = 2
        self.picking.shipping_weight = 12.5
        self.picking.note = "Entrega por la tarde"
        vals = self.carrier_mrw._prepare_mrw_shipping(self.picking)

        self.assertEqual(vals["DatosServicio"]["NumeroBultos"], 2)
        self.assertEqual(vals["DatosServicio"]["Frecuencia"], "Frecuencia 1")
        self.assertEqual(vals["DatosServicio"]["Reembolso"], "D")
        self.assertNotEqual(vals["DatosServicio"]["ImporteReembolso"], "")
        self.assertIn("Horario", vals["DatosEntrega"])

    @mock.patch(
        "odoo.addons.delivery_mrw.models.delivery_carrier.DeliveryCarrier.mrw_get_label",
        return_value={"EtiquetaFile": b"%PDF-1.4 fake PDF content"},
    )
    def test_09_stock_picking_get_label_ok(self, _mock_get_label):
        self.picking.carrier_tracking_ref = "MRW999"
        self.picking.delivery_type = "mrw"
        result = self.picking.mrw_get_label()
        self.assertEqual(result["EtiquetaFile"], b"%PDF-1.4 fake PDF content")

    def test_10_process_mrw_tracking_response_with_states(self):
        request = MRWRequest.__new__(MRWRequest)
        response_payload = {
            "Seguimiento": {
                "Abonado": [
                    {
                        "SeguimientoAbonado": {
                            "Seguimiento": [
                                {
                                    "Estado": "01",
                                    "EstadoDescripcion": "En reparto",
                                    "FechaEntrega": "01022024",
                                    "HoraEntrega": "1030",
                                },
                                {
                                    "Estado": "00",
                                    "EstadoDescripcion": "Entregado",
                                    "FechaEntrega": "02022024",
                                    "HoraEntrega": "1200",
                                },
                            ]
                        }
                    }
                ]
            }
        }
        with mock.patch(
            "odoo.addons.delivery_mrw.models.mrw_request.ZeepHelpers.serialize_object",
            return_value=response_payload,
        ):
            states = request._process_mrw_tracking_response(response={})
        self.assertEqual(len(states), 2)
        self.assertEqual(states[0]["state_code"], "01")
        self.assertEqual(states[1]["state_code"], "00")

    def test_11_process_mrw_tracking_response_without_trackings(self):
        request = MRWRequest.__new__(MRWRequest)
        response_payload = {
            "Seguimiento": {"Abonado": [{"SeguimientoAbonado": {"Seguimiento": {}}}]}
        }
        with mock.patch(
            "odoo.addons.delivery_mrw.models.mrw_request.ZeepHelpers.serialize_object",
            return_value=response_payload,
        ):
            self.assertFalse(request._process_mrw_tracking_response(response={}))

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_12_mrw_cancel_shipment_ok(self, mock_mrw_request):
        self.picking.carrier_tracking_ref = "MRW-CANCEL-001"
        mock_mrw_request.return_value._cancel_shipment.return_value = {
            "Estado": "1",
            "Mensaje": "",
        }
        self.assertTrue(self.carrier_mrw.mrw_cancel_shipment(self.picking))
        mock_mrw_request.return_value._cancel_shipment.assert_called_once_with(
            "MRW-CANCEL-001"
        )

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_13_mrw_cancel_shipment_without_tracking(self, mock_mrw_request):
        self.picking.carrier_tracking_ref = False
        self.assertTrue(self.carrier_mrw.mrw_cancel_shipment(self.picking))
        mock_mrw_request.assert_not_called()

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_14_mrw_get_label_ok(self, mock_mrw_request):
        mock_mrw_request.return_value._get_label.return_value = {
            "Estado": "1",
            "Mensaje": "",
            "EtiquetaFile": b"%PDF-1.4 fake PDF content",
        }
        label = self.carrier_mrw.mrw_get_label("MRW-LABEL-001", self.picking)
        self.assertEqual(label["EtiquetaFile"], b"%PDF-1.4 fake PDF content")
        mock_mrw_request.return_value._get_label.assert_called_once()

    def test_15_mrw_get_label_without_tracking(self):
        self.assertFalse(self.carrier_mrw.mrw_get_label(False, self.picking))

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_16_mrw_tracking_state_update_raises(self, mock_mrw_request):
        self.picking.carrier_tracking_ref = "MRW-TRACK-ERR"
        mock_mrw_request.return_value._get_tracking_states.return_value = {
            "MensajeSeguimiento": "Error de tracking",
        }
        with self.assertRaises(UserError):
            self.carrier_mrw.mrw_tracking_state_update(self.picking)

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_17_mrw_tracking_state_update_without_tracking(self, mock_mrw_request):
        self.picking.carrier_tracking_ref = False
        self.assertIsNone(self.carrier_mrw.mrw_tracking_state_update(self.picking))
        mock_mrw_request.assert_not_called()

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_18_mrw_tracking_state_update_without_states(self, mock_mrw_request):
        self.picking.carrier_tracking_ref = "MRW-TRACK-EMPTY"
        mock_mrw_request.return_value._get_tracking_states.return_value = {
            "MensajeSeguimiento": "Busqueda correcta por Número de Albarán.",
        }
        mock_mrw_request.return_value._process_mrw_tracking_response.return_value = []
        self.assertIsNone(self.carrier_mrw.mrw_tracking_state_update(self.picking))

    @mock.patch("odoo.addons.delivery_mrw.models.delivery_carrier.MRWRequest")
    def test_19_mrw_tracking_state_update_ok(self, mock_mrw_request):
        self.picking.carrier_tracking_ref = "MRW-TRACK-OK"
        delivered_dt = datetime.datetime(2024, 2, 2, 12, 0)
        mock_mrw_request.return_value._get_tracking_states.return_value = {
            "MensajeSeguimiento": "Busqueda correcta por Número de Albarán.",
        }
        mock_mrw_request.return_value._process_mrw_tracking_response.return_value = [
            {
                "state_code": "01",
                "description": "En reparto",
                "delivery_date": datetime.datetime(2024, 2, 2, 10, 30),
            },
            {
                "state_code": "00",
                "description": "Entregado",
                "delivery_date": delivered_dt,
            },
        ]

        self.carrier_mrw.mrw_tracking_state_update(self.picking)

        self.assertIn("[01] En reparto", self.picking.tracking_state_history)
        self.assertIn("[00] Entregado", self.picking.tracking_state_history)
        self.assertEqual(self.picking.tracking_state, "[00] Entregado")
        self.assertEqual(self.picking.date_delivered, delivered_dt)

    def test_20_action_get_manifest(self):
        action = self.carrier_mrw.action_get_manifest()
        self.assertEqual(action["type"], "ir.actions.act_window")
        self.assertEqual(action["res_model"], "mrw.manifest.wizard")
        self.assertEqual(action["view_mode"], "form")
        self.assertEqual(action["target"], "new")
        self.assertEqual(action["name"], self.env._("MRW Manifest"))
        wizard = self.env["mrw.manifest.wizard"].browse(action["res_id"])
        self.assertTrue(wizard.exists())
        self.assertEqual(wizard.carrier_id, self.carrier_mrw)
        view_id = self.env.ref("delivery_mrw.delivery_mrw_manifest_wizard_form").id
        self.assertEqual(action["view_id"], view_id)
        self.assertEqual(action["views"], [(view_id, "form")])
