# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import Form, common


class TestDeliverySeurBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.carrier = cls.env["delivery.carrier"].search(
            [("delivery_type", "=", "seur")]
        )
        cls.company = cls.env.company
        cls.company.country_id = cls.env.ref("base.es").id
        cls.company.partner_id.city = "Madrid"
        cls.company.partner_id.zip = "28001"
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Partner test [ñáéíóú]",
                "country_id": cls.env.ref("base.es").id,
                "street": cls.company.partner_id.street,
                "city": cls.company.partner_id.city,
                "zip": cls.company.partner_id.zip,
                "state_id": cls.company.partner_id.state_id.id,
            }
        )
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.sale = cls._create_sale_order(cls)
        cls.picking = cls.sale.picking_ids[0]
        cls.picking.move_lines.quantity_done = 1

    def _create_sale_order(self):
        order_form = Form(self.env["sale.order"])
        order_form.partner_id = self.partner
        with order_form.order_line.new() as line_form:
            line_form.product_id = self.product
            line_form.product_uom_qty = 1
        sale = order_form.save()
        if self.carrier:
            delivery_wizard = Form(
                self.env["choose.delivery.carrier"].with_context(
                    {"default_order_id": sale.id, "default_carrier_id": self.carrier.id}
                )
            ).save()
            delivery_wizard.button_confirm()
        sale.action_confirm()
        return sale


class TestDeliverySeur(TestDeliverySeurBase):
    def test_soap_connection(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without SEUR credentials")
        self.assertTrue(self.carrier.seur_test_connection())

    def test_order_seur_rate_shipment_error(self):
        with self.assertRaises(NotImplementedError):
            self.carrier.seur_rate_shipment(self.sale)

    def test_delivery_carrier_seur_integration(self):
        if not self.carrier or self.carrier.prod_environment:
            self.skipTest("Without SEUR credentials")
        self.picking.action_confirm()
        self.picking.action_assign()
        self.picking.send_to_shipper()
        self.assertEquals(self.picking.message_attachment_count, 1)
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.tracking_state_history)
        self.picking.tracking_state_update()
        self.assertEquals(
            self.picking.tracking_state_history,
            "No existen expediciones para la búsqueda realizada",
        )
        self.picking.cancel_shipment()
