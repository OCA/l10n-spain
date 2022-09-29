# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2022 Tecnativa - David Vidal
from odoo.exceptions import UserError
from odoo.tests import Form, common


class TestDeliveryCTTExpress(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.shipping_product = cls.env["product.product"].create(
            {
                "type": "service",
                "name": "Test Shipping costs",
                "list_price": 10.
            }
        )
        cls.carrier_cttexpress = cls.env["delivery.carrier"].create(
            {
                "name": "CTT Express",
                "delivery_type": "cttexpress",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
                # Test credentials
                "cttexpress_user": "",
                "cttexpress_password": "",
                "cttexpress_agency": "",
                "cttexpress_contract": "",
                "cttexpress_shipping_type": "19H",
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
        cls.sale_order.carrier_id = cls.carrier_cttexpress
        cls.sale_order.action_confirm()
        cls.picking = cls.sale_order.picking_ids
        cls.picking.move_lines.quantity_done = 20

    def test_01_cttexpress_picking_confirm_simple(self):
        """The picking is confirm and the shipping is recorded to CTT Express"""
        self.picking.button_validate()
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)

    def test_02_cttexpress_manifest(self):
        """API work although without data"""
        wizard = self.env["cttexpress.manifest.wizard"].create(
            {
                "carrier_id": self.carrier_cttexpress.id,
                "date_from": "2050-05-31"
            }
        )
        with self.assertRaises(UserError):
            wizard.get_manifest()
