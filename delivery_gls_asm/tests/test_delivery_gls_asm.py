# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
from unittest import mock

from odoo.exceptions import UserError
from odoo.tests import Form

from odoo.addons.base.tests.common import BaseCommon

request_model = "odoo.addons.delivery_gls_asm.models.gls_asm_request.GlsAsmRequest"

SHIPPING_RESPONSE = {
    "gls_sent_xml": "<Servicios/>",
    "_return": 0,
    "_codexp": "EXP0000000000001",
    "_codbarras": "BAR0000000000001",
    "Referencias": {"Referencia": [{"_tipo": "N", "value": "INT0000000000001"}]},
}
TRACKING_RESPONSE = {
    "codestado": "0",
    "estado": "MANIFESTADA",
    "tracking_list": {
        "tracking": {
            "fecha": "2026-01-01 10:00:00",
            "codigo": "0",
            "evento": "MANIFESTADA",
        }
    },
}
CANCEL_RESPONSE = {
    "gls_sent_xml": "<Servicios/>",
    "_return": 0,
    "value": "Expedición anulada",
}


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
            }
        )
        cls.sender_partner = cls.env.company.partner_id
        cls.sender_partner.write(
            {
                "street": "Calle del Almacen, 1",
                "city": "Odoo Ville",
                "zip": "28002",
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
        cls.picking.picking_type_id.warehouse_id.partner_id = cls.sender_partner
        cls.picking.move_ids.quantity = 20
        cls.picking.number_of_packages = 1

    @mock.patch(f"{request_model}._send_shipping", return_value=SHIPPING_RESPONSE)
    @mock.patch(f"{request_model}._get_tracking_states", return_value=TRACKING_RESPONSE)
    @mock.patch(f"{request_model}._cancel_shipment", return_value=CANCEL_RESPONSE)
    def test_01_gls_picking_confirm_simple(self, *args):
        """The picking is confirm and the shipping is recorded to GLS"""
        self.picking.name = "ODOO-TEST-0123456789"
        with self.assertRaises(UserError):
            self.picking.button_validate()
        self.picking.name = "ODOO-0000000001"
        self.picking.button_validate()
        self.assertEqual(self.picking.carrier_tracking_ref, "EXP0000000000001")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "BAR0000000000001")
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
