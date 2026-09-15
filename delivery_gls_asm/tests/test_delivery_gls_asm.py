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
PICKUP_RESPONSE = {
    "gls_sent_xml": "<Servicios/>",
    "_return": 0,
    "_codigo": "REC0000000000001",
}
PICKUP_TRACKING_RESPONSE = [
    {"Fecha": "2026-01-01", "Hora": "10:00", "Codigo": "1", "Descripcion": "SOLICITADA"}
]
POD_TRACKING_RESPONSE = dict(
    TRACKING_RESPONSE,
    digitalizaciones={
        "digitalizacion": {"imagen": "https://pods.gls-spain.es/pod.pdf"}
    },
)


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

    @mock.patch(f"{request_model}._send_pickup", return_value=PICKUP_RESPONSE)
    @mock.patch(
        f"{request_model}._get_pickup_tracking_states",
        return_value=PICKUP_TRACKING_RESPONSE,
    )
    def test_04_gls_pickup_confirm(self, *args):
        """A pickup is requested to GLS and tracked apart from a shipping"""
        self.carrier_gls_asm.gls_asm_service = "56"
        self.assertTrue(self.carrier_gls_asm.gls_is_pickup_service)
        self.picking.gls_asm_send_pickup()
        self.assertEqual(self.picking.carrier_tracking_ref, "REC0000000000001")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "REC0000000000001")
        self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertEqual(self.picking.gls_pickup_state, "recorded")
        self.assertEqual(self.picking.delivery_state, "shipping_recorded_in_carrier")

    def test_05_missing_street(self):
        """We can't send anything to GLS without the addresses"""
        self.sender_partner.write({"street": False, "street2": False})
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.carrier_gls_asm.gls_asm_service = "56"
        with self.assertRaises(UserError):
            self.carrier_gls_asm._prepare_gls_asm_pickup(self.picking)

    def test_06_tracking_links(self):
        """Every kind of shipping has its own tracking link"""
        self.picking.carrier_tracking_ref = "123456"
        link = self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking)
        self.assertIn("123456", link)
        self.assertIn(self.partner.zip, link)
        self.picking.gls_asm_picking_ref = "INT0000000000001"
        international_link = self.carrier_gls_asm.gls_asm_get_tracking_link(
            self.picking
        )
        self.assertIn("INT0000000000001", international_link)
        self.partner.country_id = self.env.ref("base.pt")
        portuguese_link = self.carrier_gls_asm.gls_asm_get_tracking_link(self.picking)
        self.assertIn("INT0000000000001", portuguese_link)
        self.assertNotEqual(portuguese_link, international_link)

    @mock.patch(f"{request_model}._shipping_label", return_value=b"%PDF-1.4 label")
    def test_07_label_and_manifest_action(self, *args):
        """The label is attached to the picking and the manifest wizard opens"""
        self.assertFalse(self.carrier_gls_asm.gls_asm_get_label(False))
        self.picking.gls_asm_public_tracking_ref = "BAR0000000000001"
        self.picking.gls_asm_get_label()
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", "gls_BAR0000000000001.pdf"),
            ]
        )
        self.assertTrue(attachment)
        action = self.carrier_gls_asm.action_get_manifest()
        self.assertEqual(action["res_model"], "gls.asm.minifest.wizard")
        wizard = self.env[action["res_model"]].browse(action["res_id"])
        self.assertEqual(wizard.carrier_id, self.carrier_gls_asm)

    @mock.patch(
        f"{request_model}._get_tracking_states",
        return_value=[TRACKING_RESPONSE, TRACKING_RESPONSE],
    )
    def test_08_ambiguous_tracking_ref(self, *args):
        """GLS returns several expeditions when the reference isn't unique"""
        self.picking.carrier_tracking_ref = "123456"
        with self.assertRaises(UserError):
            self.picking.cancel_shipment()

    def test_09_gls_cod(self):
        """The cash on delivery amount is taken from the sale order"""
        self.carrier_gls_asm.gls_asm_cash_on_delivery = True
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(
            float(vals.get("importes_reembolso")), self.sale_order.amount_total
        )

    @mock.patch(
        f"{request_model}._get_tracking_states", return_value=POD_TRACKING_RESPONSE
    )
    @mock.patch("odoo.addons.delivery_gls_asm.models.delivery_carrier.requests.get")
    def test_10_gls_pod(self, mock_get, *args):
        """The proof of delivery is downloaded and attached to the picking"""
        mock_get.return_value = mock.MagicMock(content=b"%PDF-1.4 pod", status_code=200)
        self.picking.carrier_tracking_ref = "123456"
        self.carrier_gls_asm.gls_asm_tracking_state_update(self.picking)
        self.assertTrue(self.picking.pod_file)
        self.assertFalse(self.picking.pod_error)
        self.assertEqual(self.picking.pod_filename, "gls_pod_123456")
