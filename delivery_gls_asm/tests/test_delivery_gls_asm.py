# Copyright 2020 Tecnativa - David Vidal
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from unittest import mock
from odoo.tests import common, Form

# We could rely on test user to make the tests, although we would rely on
# the service stability wich could break CIs
# It's better to mock the interface response and to test
# Odoo flows regressions.
_mock_class = (
    "odoo.addons.delivery_gls_asm.models.gls_asm_request.GlsAsmRequest")


class TestDeliveryGlsAsm(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env['product.product'].create({
            'type': 'service',
            'name': 'Test Shipping costs',
            'list_price': 10.0,
        })
        cls.carrier_gls_asm = cls.env['delivery.carrier'].create({
            'name': 'GLS ASM',
            'delivery_type': 'gls_asm',
            'product_id': cls.shipping_product.id,
            'prod_environment': False,
        })
        cls.product = cls.env['product.product'].create({
            'type': 'product',
            'name': 'Test product',
        })
        cls.partner = cls.env['res.partner'].create({
            'name': 'Mr. Odoo',
            'city': 'Odoo Ville',
            'zip': '28001',
            'street': 'Calle de La Rua, 3',
        })
        cls.partner_wh = cls.env['res.partner'].create({
            'name': 'WH Test Partner',
            'city': 'Odoo City',
            'zip': '08001',
            'street': 'Strasse Street, 1',
        })
        order_form = Form(
            cls.env['sale.order'].with_context(tracking_disable=True))
        order_form.partner_id = cls.partner
        order_form.carrier_id = cls.carrier_gls_asm
        with order_form.order_line.new() as line:
            line.product_id = cls.product
            line.product_uom_qty = 20.0
        cls.sale_order = order_form.save()
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_lines.quantity_done = 20

    def test_01_gls_picking_confirm_simple(self):
        """The picking is confirm and the shipping is recorded to GLS"""
        mocked_response = {
            "_codexp": "TEST123456789",
            "_codbarras": "1234567890123",
            "_return": 0,
        }
        with mock.patch(
            _mock_class + '._send_shipping',
            return_value=mocked_response,
        ):
            self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "TEST123456789")
        self.assertEqual(
            self.picking.gls_asm_public_tracking_ref, "1234567890123")
        # Cancel the expedition. The tracking refs go away
        mocked_response = {
            "_return": 0,
        }
        with mock.patch(
            _mock_class + '._cancel_shipment',
            return_value=mocked_response,
        ):
            self.picking.cancel_shipment()
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_02_gls_manifest(self):
        """Mock manifest response"""
        mocked_response = [{
            'cliente': "Pruebas WS",
            'codexp': "467247191",
            'bultos': "1",
            'kgs': "1,0",
            'nombre_dst': "Mr. Odoo",
            'calle_dst': "Test Address",
            'localidad_dst': "Test location",
            'cp_dst': "28001",
        }]
        wizard = self.env["gls.asm.minifest.wizard"].create({
            "carrier_id": self.carrier_gls_asm.id,
            "date_from": "2020-05-31",
        })
        with mock.patch(
            _mock_class + '._get_manifest',
            return_value=mocked_response,
        ):
            report = wizard.get_manifest()
            self.assertEqual(report["data"]["deliveries"], mocked_response)
