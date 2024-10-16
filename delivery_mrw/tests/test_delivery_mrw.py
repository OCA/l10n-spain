import datetime

from odoo.tests import Form, common


class TestDeliveryMRW(common.TransactionCase):
    def setUp(self):
        super().setUp()
        spain = self.env["res.country"].search([("code", "=", "ES")])
        self.env.company.partner_id.country_id = spain
        self.env.company.external_report_layout_id = self.env.ref(
            "web.external_layout_standard"
        )
        self.shipping_product = self.env["product.product"].create(
            {
                "type": "service",
                "name": "Test Shipping costs",
                "list_price": 10.0,
            }
        )
        self.carrier_mrw = self.env.ref("delivery_mrw.mrw_carrier_test")
        self.carrier_mrw.write(
            {
                "product_id": self.shipping_product.id,
                "company_id": self.env.company.id,
            }
        )
        self.product = self.env["product.product"].create(
            {
                "type": "product",
                "name": "Test product",
            }
        )
        stock_location = self.env.ref("stock.stock_location_stock")
        inventory = self.env["stock.quant"].create(
            {
                "product_id": self.product.id,
                "location_id": stock_location.id,
                "inventory_quantity": 100,
            }
        )
        inventory.action_apply_inventory()
        self.assertEqual(self.product.qty_available, 100)
        self.partner = self.env["res.partner"].create(
            {
                "name": "Mr. Odoo & Co.",
                "city": "Madrid",
                "phone": "+34 91 123 45 67",
                "zip": "28001",
                "street": "Calle de La Rua, 3",
                "street2": "4-1",
                "country_id": spain.id,
            }
        )
        order_form = Form(self.env["sale.order"].with_context(tracking_disable=True))
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line:
            line.product_id = self.product
            line.product_uom_qty = 20.0
        self.sale_order = order_form.save()
        self.sale_order.date_order = datetime.datetime.today()
        self.sale_order.carrier_id = self.carrier_mrw.id
        self.sale_order.action_confirm()
        self.picking = self.sale_order.picking_ids

    def test_01_mrw_picking_confirm_simple(self):
        """The picking is confirmed and the shipping is recorded to MRW"""
        self.assertEqual(self.product.qty_available, 100)
        self.picking.name = "picking1"
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_ids.quantity_done = self.picking.move_ids.product_uom_qty
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertEqual(self.product.qty_available, 80)
        self.assertTrue(self.picking.carrier_tracking_ref)

    def test_02_mrw_manifest(self):
        """Manifest is created"""
        self.picking.name = "picking1"
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.move_ids.quantity_done = self.picking.move_ids.product_uom_qty
        self.picking.button_validate()
        wizard = self.env["mrw.manifest.wizard"].create(
            {
                "carrier_id": self.carrier_mrw.id,
                "date_from": datetime.date.today(),
            }
        )
        manifest_data = wizard.get_manifest()["data"]["deliveries"]
        self.assertEqual(
            manifest_data[-1]["carrier_tracking_ref"], self.picking.carrier_tracking_ref
        )
