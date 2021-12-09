# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
import time

from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliveryGlsAsm(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_gls_asm = cls.env["delivery.carrier"].create(
            {
                "name": "GLS ASM",
                "delivery_type": "gls_asm",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
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
        cls.sale_order.carrier_id = cls.carrier_gls_asm.id
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_lines.quantity_done = 20

    def test_01_gls_picking_confirm_simple(self):
        """The picking is confirm and the shipping is recorded to GLS"""
        # GLS API prevents duplicated references so in order to test we need a
        # unique key that doesn't collide with any CI around, as every test really
        # records an expedition
        self.picking.name = "ODOO-TEST-{}".format(time.time())
        with self.assertRaises(UserError):
            self.picking.button_validate()
        self.picking.name = "ODOO-{}".format(int(time.time()))
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertTrue(self.picking.gls_asm_public_tracking_ref)
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)

    def test_02_gls_manifest(self):
        """API work although without data"""
        wizard = self.env["gls.asm.minifest.wizard"].create(
            {"carrier_id": self.carrier_gls_asm.id, "date_from": "2050-05-31"}
        )
        with self.assertRaises(UserError):
            wizard.get_manifest()

    def test_03_gls_escaping(self):
        """We must ensure that the values we'll be putting into the XML are
        properly escaped"""
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(vals.get("destinatario_nombre"), "Mr. Odoo &amp; Co.")
