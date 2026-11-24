# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# Copyright 2020 Tecnativa - David Vidal
# Copyright 2021 Tecnativa - Víctor Martínez
# Copyright 2026 PYMING - Extreme Micro S.L.
import base64
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import Form, TransactionCase, tagged

from .common import LABEL_PDF, GlsAsmOfflineMixin


@tagged("post_install", "-at_install")
class TestDeliveryGlsAsm(GlsAsmOfflineMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # A dedicated native chart/warehouse avoids development-company defaults.
        company = cls.env["res.company"].create({"name": "Synthetic GLS Company"})
        cls.env.user.company_ids |= company
        cls.env["account.chart.template"].try_loading(
            "generic_coa", company=company, install_demo=False
        )
        cls.env = cls.env(
            context=dict(cls.env.context, allowed_company_ids=company.ids)
        )
        company.stock_move_email_validation = False
        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", company.id)], limit=1
        )
        cls.sender = cls.env["res.partner"].create(
            {
                "name": "Synthetic Sender",
                "street": "Sender Street 1",
                "city": "Madrid",
                "zip": "28001",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.warehouse.partner_id = cls.sender
        cls.warehouse.out_type_id.print_label = True
        cls.category = cls.env["product.category"].create(
            {"name": "Synthetic GLS Products", "property_valuation": "manual_periodic"}
        )
        cls.shipping_product = cls.env["product.product"].create(
            {"type": "service", "name": "Test Shipping costs", "list_price": 10.0}
        )
        cls.carrier_gls_asm = cls.env["delivery.carrier"].create(
            {
                "name": "GLS ASM",
                "delivery_type": "gls_asm",
                "product_id": cls.shipping_product.id,
                "prod_environment": False,
                "integration_level": "rate_and_ship",
                "gls_asm_shiptime": "3",
            }
        )
        cls.product = cls.env["product.product"].create(
            {"type": "product", "name": "Test product", "categ_id": cls.category.id}
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
        cls.picking.move_ids.quantity = 20
        cls.picking.move_ids.picked = True
        cls.picking.number_of_packages = 1

    def test_01_gls_picking_confirm_simple(self):
        """Validate, book, track, label and cancel through offline business flows."""
        encoded_label = base64.b64encode(LABEL_PDF).decode()
        self._allow_soap(
            GrabaServicios=[
                self._booking_response(
                    "TEST-EXP", "TEST-BARCODE", "TEST-REF", encoded_label
                )
            ],
            GetExpCli=[
                self._tracking_response("-10"),
                self._tracking_response("5"),
            ],
            Anula=[
                '<response><Servicios><Envio><Resultado return="0">'
                "Synthetic cancellation</Resultado></Envio></Servicios></response>"
            ],
            EtiquetaEnvio=[
                # The WSDL returns ArrayOfBase64Binary; two entries retain its list.
                f"<response><base64Binary>{encoded_label}</base64Binary>"
                f"<base64Binary>{encoded_label}</base64Binary></response>"
            ],
        )
        # Preserve the original long-reference guard, without a live expedition.
        self.picking.name = "ODOO-TEST-REFERENCE-TOO-LONG"
        with self.assertRaisesRegex(UserError, "15 characters"):
            # Restore done moves after the rejected validation, as an RPC would.
            with self.env.cr.savepoint():
                self.picking.button_validate()
        self.soap_service.GrabaServicios.assert_not_called()
        self.picking.name = "ODOO-TEST-1"
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertTrue(self.picking.carrier_tracking_ref)
        self.assertTrue(self.picking.gls_asm_public_tracking_ref)
        self.assertEqual(self.picking.carrier_tracking_ref, "TEST-EXP")
        self.assertEqual(self.picking.gls_asm_public_tracking_ref, "TEST-BARCODE")
        self.assertEqual(self.picking.gls_asm_picking_ref, "TEST-REF")
        self._assert_label("gls_label_TEST-BARCODE.pdf")
        self.assertEqual(
            [call[0] for call in self.soap_service.method_calls], ["GrabaServicios"]
        )
        self.picking.gls_asm_get_label()
        self._assert_label("gls_TEST-BARCODE.pdf")
        self.soap_service.EtiquetaEnvio.assert_called_once_with("TEST-BARCODE", "PDF")
        self.picking.cancel_shipment()
        self.assertFalse(self.picking.carrier_tracking_ref)
        self.assertFalse(self.picking.gls_asm_public_tracking_ref)
        self.assertFalse(self.picking.gls_asm_picking_ref)
        self.assertEqual(self.picking.delivery_state, "canceled_shipment")
        self.assertEqual(self.picking.gls_shipment_state, "cancel")
        self.assertIn("[5] Synthetic canceled", self.picking.tracking_state_history)
        self.soap_service.GrabaServicios.assert_called_once()
        self.assertEqual(self.soap_service.GetExpCli.call_count, 2)
        self.soap_service.GetExpCli.assert_called_with(
            codigo="TEST-EXP", uid="SYNTHETIC"
        )
        self.soap_service.Anula.assert_called_once()
        self.assertIn(
            'referencia="TEST-EXP"',
            str(self.soap_service.Anula.call_args.kwargs["docIn"]),
        )

    def _assert_label(self, name):
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", name),
            ]
        )
        self.assertEqual(len(attachment), 1)
        self.assertEqual(base64.b64decode(attachment.datas), LABEL_PDF)
        self.assertFalse(attachment.store_fname)

    def _tracking_response(self, code):
        state = "Synthetic recorded" if code == "-10" else "Synthetic canceled"
        return f"""<response><expediciones><exp>
            <codestado>{code}</codestado><estado>{state}</estado>
            <tracking_list><tracking>
                <fecha>01/01/2026 12:00</fecha><codigo>{code}</codigo>
                <evento>{state}</evento>
            </tracking></tracking_list>
        </exp></expediciones></response>"""

    def test_02_gls_manifest(self):
        """An empty manifest raises the original error without contacting GLS."""
        wizard = self.env["gls.asm.minifest.wizard"].create(
            {
                "carrier_id": self.carrier_gls_asm.id,
                "date_from": fields.Date.today() + timedelta(days=1),
            }
        )
        with self.assertRaises(UserError):
            wizard.get_manifest()

    def test_03_gls_escaping(self):
        """We must ensure that the values we'll be putting into the XML are
        properly escaped"""
        vals = self.carrier_gls_asm._prepare_gls_asm_shipping(self.picking)
        self.assertEqual(vals.get("destinatario_nombre"), "Mr. Odoo &amp; Co.")
