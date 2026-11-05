import datetime
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools import mute_logger

from odoo.addons.base.tests.common import BaseCommon


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
    def test_01_mrw_picking_confirm_simple(self, mock, *arg):
        """The picking is confirmed and the shipping is recorded to MRW"""
        self.picking.name = "picking1"
        self.picking.number_of_packages = 1
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_ids.quantity = self.picking.move_ids.product_uom_qty
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.product.qty_available, 80)
        self.assertTrue(self.picking.carrier_tracking_ref)

    @mock.patch("odoo.addons.delivery_mrw.models.mrw_request.Client")
    @mock.patch(
        "odoo.addons.delivery_mrw.models.delivery_carrier.DeliveryCarrier.mrw_get_label",
        return_value={
            "EtiquetaFile": b"%PDF-1.4 fake PDF content",
        },
    )
    def test_02_mrw_manifest(self, mock, *arg):
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

    def test_03_mrw_address_national(self):
        """Street type, number and floor/door are split for national shipments"""
        address = self.carrier_mrw.mrw_address(self.partner, international=False)
        self.assertEqual(address["Via"].strip(), "Calle de La Rua")
        self.assertEqual(address["Numero"], "3")
        self.assertEqual(address["Resto"], "4-1")
        self.assertEqual(address["CodigoPostal"], "28001")
        self.assertEqual(address["Poblacion"], "Madrid")
        self.partner.write({"street": "C/ Mayor 12, 3º 2ª", "street2": False})
        address = self.carrier_mrw.mrw_address(self.partner, international=False)
        self.assertEqual(address["CodigoTipoVia"], "C/")
        self.assertEqual(address["Via"].strip(), "Mayor")
        self.assertEqual(address["Numero"], "12")
        self.assertEqual(address["Resto"].strip(), "3º 2ª")

    def test_04_mrw_address_without_number(self):
        """Streets without number (s/n) are sent with number 0"""
        self.partner.write({"street": "Camino Viejo s/n", "street2": False})
        address = self.carrier_mrw.mrw_address(self.partner, international=False)
        self.assertEqual(address["Via"].strip(), "Camino Viejo")
        self.assertEqual(address["Numero"], "0")

    def test_05_mrw_address_errors(self):
        """Number ranges and missing streets are rejected"""
        self.partner.write({"street": "Avenida Diagonal 12-14"})
        with self.assertRaises(UserError):
            self.carrier_mrw.mrw_address(self.partner, international=False)
        self.partner.write({"street": False})
        with self.assertRaises(UserError):
            self.carrier_mrw.mrw_address(self.partner, international=False)

    def test_06_mrw_address_international(self):
        """International shipments send the whole street and the country code"""
        address = self.carrier_mrw.mrw_address(self.partner, international=True)
        self.assertEqual(address["CodigoPais"], "ES")
        self.assertEqual(address["CodigoPostal"], "28001")
        self.assertNotIn("Numero", address)

    def test_07_mrw_check_response(self):
        """Error responses raise and successful ones return their message"""
        with self.assertRaisesRegex(UserError, "MRW Error: Boom"):
            self.carrier_mrw._mrw_check_response({"Estado": "0", "Mensaje": "Boom"})
        self.assertEqual(
            self.carrier_mrw._mrw_check_response({"Estado": "1", "Mensaje": "OK"}),
            "OK",
        )

    def test_08_mrw_get_tracking_link(self):
        """The tracking link depends on the national/international setting"""
        self.picking.carrier_tracking_ref = "123456"
        self.assertIn(
            "modo=nacional&envio=123456",
            self.carrier_mrw.mrw_get_tracking_link(self.picking),
        )
        self.carrier_mrw.international_shipping = True
        self.assertIn(
            "modo=internacional&envio=123456",
            self.carrier_mrw.mrw_get_tracking_link(self.picking),
        )

    def _mrw_tracking_response(self, trackings):
        return {
            "MensajeSeguimiento": "Busqueda correcta por Número de Albarán.",
            "Seguimiento": {
                "Abonado": [{"SeguimientoAbonado": {"Seguimiento": trackings}}]
            },
        }

    @mock.patch("odoo.addons.delivery_mrw.models.mrw_request.Client")
    def test_09_mrw_tracking_state_update(self, client_mock):
        """Tracking states from MRW are parsed and written to the picking"""
        get_envios = client_mock.return_value.service.GetEnvios
        get_envios.return_value = self._mrw_tracking_response(
            [
                {"Estado": "05", "EstadoDescripcion": "Recogido"},
                {
                    "Estado": "02",
                    "EstadoDescripcion": "En tránsito",
                    "FechaEntrega": "31022026",
                },
                {
                    "Estado": "01",
                    "EstadoDescripcion": "En reparto",
                    "FechaEntrega": "22092026",
                },
                {
                    "Estado": "00",
                    "EstadoDescripcion": "Entregado",
                    "FechaEntrega": "22092026",
                    "HoraEntrega": "1145",
                },
            ]
        )
        self.picking.carrier_tracking_ref = "123456"
        with mute_logger("odoo.addons.delivery_mrw.models.mrw_request"):
            self.picking.tracking_state_update()
        request = get_envios.call_args.kwargs
        self.assertEqual(request["login"], self.carrier_mrw.mrw_username)
        self.assertEqual(request["valorFiltroDesde"], "123456")
        history = self.picking.tracking_state_history.splitlines()
        self.assertEqual(len(history), 4)
        self.assertEqual(history[2], "22/09/2026 00:00 - [01] En reparto")
        self.assertEqual(history[3], "22/09/2026 11:45 - [00] Entregado")
        self.assertEqual(self.picking.tracking_state, "[00] Entregado")
        self.assertEqual(
            self.picking.date_delivered, datetime.datetime(2026, 9, 22, 11, 45)
        )

    @mock.patch("odoo.addons.delivery_mrw.models.mrw_request.Client")
    def test_10_mrw_tracking_state_update_errors(self, client_mock):
        """Pickings without reference or states are left untouched, errors raise"""
        self.picking.tracking_state_update()
        client_mock.assert_not_called()
        self.picking.carrier_tracking_ref = "123456"
        get_envios = client_mock.return_value.service.GetEnvios
        get_envios.return_value = {"MensajeSeguimiento": "No se han encontrado envíos"}
        with self.assertRaisesRegex(UserError, "No se han encontrado envíos"):
            self.picking.tracking_state_update()
        get_envios.return_value = {
            "MensajeSeguimiento": "Busqueda correcta por Número de Albarán.",
            "Seguimiento": {"Abonado": []},
        }
        self.picking.tracking_state_update()
        self.assertFalse(self.picking.tracking_state)
        get_envios.return_value = self._mrw_tracking_response([])
        self.picking.tracking_state_update()
        self.assertFalse(self.picking.tracking_state)

    @mock.patch("odoo.addons.delivery_mrw.models.mrw_request.Client")
    def test_11_mrw_picking_get_label(self, client_mock):
        """The label button fetches the label from MRW and posts it in the chatter"""
        label = {
            "Estado": "1",
            "Mensaje": "",
            "EtiquetaFile": b"%PDF-1.4 fake PDF content",
        }
        service = client_mock.return_value.service
        service.__getitem__.return_value.return_value = label
        self.assertIsNone(self.picking.mrw_get_label())
        client_mock.assert_not_called()
        self.picking.carrier_tracking_ref = "123456"
        self.assertEqual(self.picking.mrw_get_label(), label)
        service.__getitem__.assert_called_once_with("EtiquetaEnvio")
        request = service.__getitem__.return_value.call_args.kwargs["request"]
        self.assertEqual(request["NumeroEnvio"], "123456")
        self.assertEqual(
            request["ReportTopMargin"], self.carrier_mrw.mrw_label_top_margin
        )
        message = self.picking.message_ids.filtered("attachment_ids")
        self.assertEqual(len(message), 1)
        self.assertIn("MRW Shipping Label:", message.body)
        self.assertEqual(message.attachment_ids.name, "mrw_label_123456.pdf")
        self.assertEqual(message.attachment_ids.raw, b"%PDF-1.4 fake PDF content")
