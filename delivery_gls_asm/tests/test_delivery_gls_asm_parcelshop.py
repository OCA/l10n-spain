# Copyright 2026 PYMING - Extreme Micro S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged

from ..models import delivery_carrier, gls_asm_request
from .common import LABEL_PDF, GlsAsmOfflineMixin


@tagged("post_install", "-at_install")
class TestDeliveryGlsAsmParcelshop(GlsAsmOfflineMixin, TransactionCase):
    """Synthetic fixtures and mocked SOAP only: never record a live expedition."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Error messages are asserted in English, whatever the user language.
        cls.env = cls.env(context=dict(cls.env.context, lang="en_US"))
        cls.country = cls.env.ref("base.es")
        cls.sender = cls.env["res.partner"].create(
            {
                "name": "Synthetic Sender",
                "street": "Sender Street 1",
                "city": "Madrid",
                "zip": "28001",
                "country_id": cls.country.id,
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Synthetic Customer & Co.",
                "street": "Customer Street 2",
                "city": "Madrid",
                "zip": "28002",
                "country_id": cls.country.id,
                "phone": "910000000",
                "mobile": "600000000",
                "email": "synthetic@example.test",
            }
        )
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.env.company.id)], limit=1
        )
        cls.warehouse.partner_id = cls.sender
        cls.warehouse.out_type_id.print_label = True
        cls.env.company.stock_move_email_validation = False
        cls.shipping_product = cls.env["product.product"].create(
            {"name": "Synthetic Shipping", "type": "service"}
        )
        cls.product = cls.env["product.product"].create(
            {"name": "Synthetic Parcel", "type": "consu", "weight": 1.0}
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Synthetic GLS ParcelShop",
                "delivery_type": "gls_asm",
                "product_id": cls.shipping_product.id,
                "gls_asm_service": "1",
                "gls_asm_shiptime": "19",
                "integration_level": "rate_and_ship",
            }
        )

    def setUp(self):
        super().setUp()
        self.picking = self._make_picking("PS-TEST-1", "001234")

    def _make_picking(self, name, code=False):
        return self.env["stock.picking"].create(
            {
                "name": name,
                "partner_id": self.partner.id,
                "picking_type_id": self.warehouse.out_type_id.id,
                "location_id": self.warehouse.lot_stock_id.id,
                "location_dest_id": self.env.ref("stock.stock_location_customers").id,
                "carrier_id": self.carrier.id,
                "number_of_packages": 1,
                "gls_asm_parcelshop_code": code,
                "gls_shipping_notes": "Synthetic delivery note",
                "move_ids": [
                    Command.create(
                        {
                            "name": "Synthetic Parcel",
                            "product_id": self.product.id,
                            "product_uom": self.product.uom_id.id,
                            "product_uom_qty": 2.0,
                            "location_id": self.warehouse.lot_stock_id.id,
                            "location_dest_id": self.env.ref(
                                "stock.stock_location_customers"
                            ).id,
                        }
                    )
                ],
            }
        )

    def _shipping_xml(self, values):
        # Serialization does not need to construct the network client.
        request = gls_asm_request.GlsAsmRequest.__new__(gls_asm_request.GlsAsmRequest)
        return request._prepare_send_shipping_docin(uidcustomer="SYNTHETIC", **values)

    def test_native_code_in_shipping_payload(self):
        values = self.carrier._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(values["servicio"], "1")
        self.assertEqual(values["horario"], "19")
        self.assertEqual(values["destinatario_codigo"], "001234")
        self.assertEqual(values["destinatario_nombre"], "Synthetic Customer &amp; Co.")
        self.assertEqual(values["destinatario_direccion"], self.partner.street)
        self.assertEqual(values["destinatario_cp"], self.partner.zip)
        self.assertEqual(values["destinatario_telefono"], self.partner.phone)
        self.assertEqual(values["destinatario_movil"], self.partner.mobile)
        self.assertEqual(values["destinatario_email"], self.partner.email)
        root = etree.fromstring(self._shipping_xml(values).encode())
        ns = {"gls": "http://www.asmred.com/"}
        self.assertEqual(
            root.findtext("gls:Envio/gls:Destinatario/gls:Codigo", namespaces=ns),
            "001234",
        )
        self.assertEqual(
            root.findtext("gls:Envio/gls:Destinatario/gls:Nombre", namespaces=ns),
            self.partner.name,
        )
        label = root.find("gls:Envio/gls:DevuelveAdicionales/gls:Etiqueta", ns)
        self.assertEqual(label.get("tipo"), "PDF")
        # The only differences from Express are the selected time and shop code.
        self.carrier.gls_asm_shiptime = "3"
        express = self.carrier._prepare_gls_asm_shipping(self.picking)
        values.update({"horario": "3", "destinatario_codigo": ""})
        self.assertEqual(values, express)
        self.client.assert_not_called()

    def test_express_ignores_parcelshop_code(self):
        self.carrier.gls_asm_shiptime = "3"
        before = self._shipping_xml(
            self.carrier._prepare_gls_asm_shipping(self.picking)
        )
        self.picking.gls_asm_parcelshop_code = "not a shop code"
        after = self._shipping_xml(self.carrier._prepare_gls_asm_shipping(self.picking))
        self.assertEqual(before, after)
        self.assertIn("<Codigo></Codigo>", after)
        self.client.assert_not_called()

    def test_missing_code_preflight(self):
        for code in (
            False,
            "",
            "1234567",
            "12a",
            "12 3",
            " 123",
            "123 ",
            "12\n3",
            "-123",
            "１２３",
            "١٢٣",
        ):
            with self.subTest(code=code):
                self.picking.gls_asm_parcelshop_code = code
                with patch.object(delivery_carrier, "GlsAsmRequest") as request:
                    with self.assertRaisesRegex(UserError, "1 to 6 ASCII digits"):
                        self.carrier.gls_asm_send_shipping(self.picking)
                    request.assert_not_called()
                with self.assertRaises(UserError):
                    self.carrier._prepare_gls_asm_shipping(self.picking)
        self.client.assert_not_called()

    def test_valid_code_lengths_and_leading_zeros(self):
        for code in ("0", "12345", "000001", "123456"):
            with self.subTest(code=code):
                self.picking.gls_asm_parcelshop_code = code
                values = self.carrier._prepare_gls_asm_shipping(self.picking)
                self.assertEqual(values["destinatario_codigo"], code)
        self.client.assert_not_called()

    def test_entire_batch_checked_before_client(self):
        invalid = self._make_picking("PS-TEST-2")
        with patch.object(delivery_carrier, "GlsAsmRequest") as request:
            with self.assertRaisesRegex(UserError, "PS-TEST-2"):
                self.carrier.gls_asm_send_shipping(self.picking | invalid)
            request.assert_not_called()
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.client.assert_not_called()

    def test_pickup_and_shopreturn_configuration_rejected(self):
        for service in ("7", "58"):
            with self.subTest(service=service):
                self.carrier.gls_asm_service = service
                with patch.object(delivery_carrier, "GlsAsmRequest") as request:
                    for method in (
                        self.carrier.gls_asm_send_shipping,
                        self.carrier.gls_asm_send_pickup,
                    ):
                        with self.assertRaisesRegex(UserError, "ShopReturn"):
                            method(self.picking)
                    request.assert_not_called()
                with self.assertRaises(UserError):
                    self.carrier._prepare_gls_asm_shipping(self.picking)
        self.client.assert_not_called()

    def test_service_is_not_silently_changed_or_whitelisted(self):
        self.carrier.gls_asm_service = "96"
        values = self.carrier._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(values["servicio"], "96")
        self.assertEqual(self.carrier.gls_asm_service, "96")

    def test_mocked_booking_response_and_pdf_attachment(self):
        pdf = LABEL_PDF
        # Only the client boundary is mocked: real suds conversion and PDF decoding.
        self._allow_soap(
            GrabaServicios=[
                self._booking_response(
                    "TEST-EXP",
                    "TEST-BARCODE",
                    "TEST-PICKING",
                    base64.b64encode(pdf).decode(),
                )
            ],
        )
        self.picking.send_to_shipper()
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls], ["GrabaServicios"]
        )
        self.assertEqual(self.picking.carrier_tracking_ref, "TEST-EXP")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "TEST-BARCODE")
        self.assertEqual(self.picking.gls_asm_picking_ref, "TEST-PICKING")
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", "gls_label_TEST-BARCODE.pdf"),
            ]
        )
        self.assertEqual(len(attachment), 1)
        self.assertEqual(base64.b64decode(attachment.datas), pdf)
        self.assertFalse(attachment.store_fname)
        soap = self.client.return_value.service.GrabaServicios
        soap.assert_called_once()
        self.assertIn("<Codigo>001234</Codigo>", str(soap.call_args.kwargs["docIn"]))
        with self.assertRaises(UserError):
            self.picking.gls_asm_parcelshop_code = "999999"

    def test_duplicate_error_propagates_without_recovery(self):
        self._allow_soap(
            GrabaServicios=[
                "<response><Servicios><Envio>"
                '<Resultado return="-118" />'
                "</Envio></Servicios></response>"
            ]
        )
        name = self.picking.name
        with self.assertRaisesRegex(UserError, "customer reference is duplicated"):
            self.picking.send_to_shipper()
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls], ["GrabaServicios"]
        )
        self.soap_service.GetExpCli.assert_not_called()
        self.assertEqual(self.picking.name, name)
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertFalse(self.picking.gls_asm_picking_ref)
        self.assertFalse(
            self.env["ir.attachment"].search(
                [("res_model", "=", "stock.picking"), ("res_id", "=", self.picking.id)]
            )
        )

    def test_express_booking_without_parcelshop_code(self):
        self.carrier.gls_asm_shiptime = "3"
        self.picking.gls_asm_parcelshop_code = False
        with patch.object(delivery_carrier, "GlsAsmRequest") as request:
            request.return_value._send_shipping.return_value = {
                "_return": 0,
                "_codexp": "TEST-EXPRESS",
                "_codbarras": "TEST-EXPRESS-BARCODE",
            }
            self.picking.send_to_shipper()
            values = request.return_value._send_shipping.call_args.args[0]
            self.assertEqual(values["horario"], "3")
            self.assertEqual(values["destinatario_codigo"], "")
        self.assertEqual(self.picking.carrier_tracking_ref, "TEST-EXPRESS")
        self.client.assert_not_called()

    def test_parcelshop_field_in_compiled_picking_form(self):
        view = self.env["stock.picking"].get_view(
            view_id=self.env.ref("stock.view_picking_form").id, view_type="form"
        )
        root = etree.fromstring(view["arch"].encode())
        field = root.xpath("//field[@name='gls_asm_parcelshop_code']")
        self.assertEqual(len(field), 1)
        self.assertIn("gls_asm_carrier_shiptime", field[0].get("invisible"))
        self.assertIn("picking_type_code", field[0].get("required"))
        self.assertIn("done", field[0].get("readonly"))
        self.assertIn("gls_asm_public_tracking_ref", field[0].get("readonly"))
        self.assertTrue(root.xpath("//field[@name='gls_asm_carrier_shiptime']"))

    def test_booked_code_is_immutable(self):
        for reference in (
            "carrier_tracking_ref",
            "gls_asm_public_tracking_ref",
            "gls_asm_picking_ref",
        ):
            with self.subTest(reference=reference):
                self.picking.write({reference: "SYNTHETIC-REF"})
                with self.assertRaises(UserError):
                    self.picking.gls_asm_parcelshop_code = "999999"
                with self.assertRaises(UserError):
                    self.picking.gls_asm_parcelshop_code = False
                # Same-code synchronization and ordinary writes remain possible.
                self.picking.write(
                    {
                        "gls_asm_parcelshop_code": "001234",
                        "gls_shipping_notes": "Updated synthetic note",
                    }
                )
                self.picking.write({reference: False})
        self.picking.gls_asm_parcelshop_code = "000002"
        self.assertEqual(self.picking.gls_asm_parcelshop_code, "000002")
        self.client.assert_not_called()

    def test_batch_immutability_is_atomic(self):
        unbooked = self._make_picking("PS-TEST-2", "001234")
        self.picking.gls_asm_public_tracking_ref = "TEST-BARCODE"
        with self.assertRaises(UserError):
            (unbooked | self.picking).write({"gls_asm_parcelshop_code": "999999"})
        self.assertEqual(unbooked.gls_asm_parcelshop_code, "001234")

    def test_backorder_copies_code_not_booking_references(self):
        self.picking.action_confirm()
        self.picking.write(
            {
                "carrier_tracking_ref": "TEST-EXP",
                "gls_asm_public_tracking_ref": "TEST-BARCODE",
                "gls_asm_picking_ref": "TEST-PICKING",
            }
        )
        backorder = self.picking._create_backorder()
        self.assertEqual(len(backorder), 1)
        self.assertEqual(backorder.backorder_id, self.picking)
        self.assertEqual(backorder.gls_asm_parcelshop_code, "001234")
        self.assertEqual(backorder.gls_asm_carrier_shiptime, "19")
        self.assertFalse(backorder.carrier_tracking_ref)
        self.assertFalse(backorder.gls_asm_public_tracking_ref)
        self.assertFalse(backorder.gls_asm_picking_ref)
        backorder.gls_asm_parcelshop_code = "000002"
        self.client.assert_not_called()

    def test_native_incoming_return_does_not_book(self):
        self.warehouse.out_type_id.print_label = False
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 2.0
        self.picking.move_ids.picked = True
        self.picking._action_done()
        wizard = Form(
            self.env["stock.return.picking"].with_context(
                active_id=self.picking.id,
                active_ids=self.picking.ids,
                active_model="stock.picking",
            )
        ).save()
        return_id, _return_type = wizard._create_returns()
        returned = self.env["stock.picking"].browse(return_id)
        self.assertEqual(returned.picking_type_code, "incoming")
        self.assertFalse(returned.carrier_id)
        self.assertFalse(returned.carrier_tracking_ref)
        # Even if a carrier is manually set, native incoming validation never books.
        returned.carrier_id = self.carrier
        returned.gls_asm_parcelshop_code = False
        returned.picking_type_id.print_label = True
        returned.move_ids.quantity = 2.0
        returned.move_ids.picked = True
        returned._action_done()
        self.assertFalse(returned.carrier_tracking_ref)
        self.client.assert_not_called()
