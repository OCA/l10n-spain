# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
import time

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon


class TestDeliveryGlsAsm(BaseCommon):
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
                "gls_asm_service": "37",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"is_storable": True, "name": "Test product"}
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Odoo Ville",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
                "phone": "666555444",
                "email": "test@test.com",
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
        cls.picking.move_ids.quantity = 20
        cls.picking.number_of_packages = 1
        cls.company = cls.env.user.company_id
        cls.company.partner_id.street = "Avinguda Diagonal, 405"
        cls.company.partner_id.city = "Barcelona"
        cls.company.partner_id.zip = "08008"

    def test_01_gls_picking_confirm_simple(self):
        """The picking is confirm and the shipping is recorded to GLS"""
        # GLS API prevents duplicated references so in order to test we need a
        # unique key that doesn't collide with any CI around, as every test really
        # records an expedition
        self.picking.name = f"ODOO-TEST-{time.time()}"
        with self.assertRaises(UserError):
            self.picking.button_validate()
        self.picking.name = f"ODOO-{int(time.time())}"
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertTrue(self.picking.gls_asm_public_tracking_ref)
        # Check label generation
        self.picking.gls_asm_get_label()
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "like", "gls_%"),
            ]
        )
        self.assertTrue(attachment, "Label was not attached to the picking")
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

    def test_04_gls_pickup_confirm(self):
        """Test pickup confirmation"""
        self.carrier_gls_asm.gls_asm_service = "56"  # RECOGIDA ECONOMY
        self.picking.name = f"ODOO-{int(time.time())}"
        self.picking.gls_asm_send_pickup()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertTrue(self.picking.gls_asm_public_tracking_ref)
        self.picking.cancel_shipment()
        # TODO: The pickup cancelation returns Error -204, check if
        # _prepare_cancel_pickup_docin is correct
        # self.assertFalse(self.picking.carrier_tracking_ref)
        # self.assertFalse(self.picking.gls_asm_public_tracking_ref)

    def test_05_gls_errors(self):
        """Test various error conditions"""
        self.carrier_gls_asm.gls_asm_service = "37"  # ECONOMY
        # Test missing sender street
        original_street = self.company.partner_id.street
        self.company.partner_id.street = False
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.carrier_gls_asm.gls_asm_service = "57"  # RECOGIDA ECONOMY
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_pickup(self.picking)
        self.company.partner_id.street = original_street

    def test_06_tracking_links(self):
        """Test tracking link generation"""
        self.picking.carrier_tracking_ref = "123456"
        # ASM Link
        link = self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking)
        self.assertIn("123456", link)
        self.assertIn(self.partner.zip, link)

        # International Link
        self.picking.gls_asm_picking_ref = "REFERENCIA_INT"
        link = self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking)
        self.assertIn("REFERENCIA_INT", link)

        # Portugal Link
        self.partner.country_id = self.env.ref("base.pt")
        link = self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking)
        self.assertIn("REFERENCIA_INT", link)

    def test_07_labels_and_manifests(self):
        """Test labels and manifest wizard"""
        # Labels (mocked or at least checking the branch)
        label = self.carrier_gls_asm.gls_asm_get_label("123")
        self.assertFalse(label)  # Should be false if not real tracking or mocked

        # Manifest wizard
        action = self.carrier_gls_asm.action_get_manifest()
        self.assertEqual(action["res_model"], "gls.asm.minifest.wizard")
        wizard = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(wizard.carrier_id, self.carrier_gls_asm)

        # Should raise error if no data found for manifest
        wizard.date_from = "2050-01-01"
        with self.assertRaises(UserError):
            wizard.get_manifest()

    def test_08_ambiguous_tracking_ref(self):
        """Test cancellation when tracking ref is not unique"""
        self.picking.carrier_tracking_ref = "123456"
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()

    def test_09_gls_cod(self):
        """Test Cash On Delivery"""
        self.carrier_gls_asm.gls_asm_cash_on_delivery = True
        # Need a sales order for COD amount
        sale = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": self.product.id,
                            "product_uom_qty": 1,
                            "price_unit": 100.0,
                        },
                    )
                ],
            }
        )
        sale.action_confirm()
        self.picking = sale.picking_ids[0]
        self.picking.carrier_id = self.carrier_gls_asm
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(vals.get("destinatario_nombre"), "Mr. Odoo &amp; Co.")
