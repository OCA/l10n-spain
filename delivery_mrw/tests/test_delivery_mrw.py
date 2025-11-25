import datetime
from unittest import mock

from odoo.tests import Form

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
            {"type": "product", "name": "Test product"}
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
