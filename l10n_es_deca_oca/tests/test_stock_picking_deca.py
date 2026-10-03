# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
from unittest.mock import patch

from pypdf import PdfWriter

from odoo.tests import Form
from odoo.tests.common import TransactionCase

from odoo.addons.base.models.ir_actions_report import IrActionsReport


class TestStockPickingDeca(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        # Create partner
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test Partner",
            }
        )

        # Create carrier contact
        cls.carrier_contact = cls.env["res.partner"].create(
            {
                "name": "Carrier Contact",
            }
        )

        # Create carrier (mock basic delivery carrier)
        cls.carrier_product = cls.env["product.product"].create(
            {
                "name": "Carrier Product",
                "type": "service",
            }
        )
        cls.carrier = cls.env["delivery.carrier"].create(
            {
                "name": "Test Carrier",
                "product_id": cls.carrier_product.id,
                "carrier_contact_id": cls.carrier_contact.id,
            }
        )

        # Create product and stock location for picking
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
            }
        )

        cls.location_customer = cls.env.ref("stock.stock_location_customers")
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

        # Create a picking
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_out.id,
                "location_id": cls.location_stock.id,
                "location_dest_id": cls.location_customer.id,
                "carrier_id": cls.carrier.id,
                "tractor_license_plate": "1111AAA",
                "trailer_license_plate": "R1111BBB",
                "special_authorization": "AUTH-123",
            }
        )

        # Add a move to the picking
        cls.move = cls.env["stock.move"].create(
            {
                "product_id": cls.product.id,
                "product_uom_qty": 10.0,
                "product_uom": cls.product.uom_id.id,
                "picking_id": cls.picking.id,
                "location_id": cls.location_stock.id,
                "location_dest_id": cls.location_customer.id,
            }
        )

    def test_01_carrier_contact_compute(self):
        """Test if the carrier_contact_id is properly computed from the carrier."""
        self.assertEqual(
            self.picking.carrier_contact_id,
            self.carrier_contact,
            "Carrier contact should be computed from the carrier.",
        )

    def test_02_picking_history_logs(self):
        """Test history logging for license plates and authorizations."""
        # Logs shouldn't happen when picking is in draft/waiting
        self.picking.tractor_license_plate = "2222CCC"
        self.assertFalse(self.picking.tractor_license_plate_history)

        # Confirm and validate picking
        self.picking.action_confirm()
        self.picking.move_ids.quantity = 10.0
        self.picking.button_validate()

        self.assertEqual(self.picking.state, "done")

        # Now change the plate, history should trigger
        self.picking.tractor_license_plate = "3333DDD"
        self.assertIn("2222CCC", self.picking.tractor_license_plate_history)

        # Change trailer
        self.picking.trailer_license_plate = "R2222EEE"
        self.assertIn("R1111BBB", self.picking.trailer_license_plate_history)

        # Change authorization
        self.picking.special_authorization = "AUTH-456"
        self.assertIn("AUTH-123", self.picking.special_authorization_history)

        # Change plate again to ensure multiline appending works
        self.picking.tractor_license_plate = "4444FFF"
        self.assertIn("2222CCC", self.picking.tractor_license_plate_history)
        self.assertIn("3333DDD", self.picking.tractor_license_plate_history)

    def test_03_get_share_url(self):
        """Test generation of DeCA access token and URL."""
        self.assertFalse(self.picking.deca_access_token)
        url = self.picking._get_share_url()
        self.assertTrue(
            self.picking.deca_access_token, "Access token should be generated"
        )
        self.assertIn(f"/my/picking/{self.picking.id}", url)
        self.assertIn(f"access_token={self.picking.deca_access_token}", url)

    def test_04_deca_immutability_and_versions(self):
        """Test PDF generations increment deca_version and create attachments."""
        report = self.env["ir.actions.report"]

        # Create a valid empty PDF for testing without wkhtmltopdf
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        out = io.BytesIO()
        writer.write(out)
        dummy_pdf = out.getvalue()

        with patch.object(
            IrActionsReport, "_render_qweb_pdf", return_value=(dummy_pdf, "pdf")
        ):
            # Initially version is 0
            self.assertEqual(self.picking.deca_version, 0)

            # 1. First print -> should generate v1
            pdf_1, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(self.picking.deca_version, 1)
            self.assertTrue(self.picking.deca_content_hash)

            # Check attachment exists
            att_v1 = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "stock.picking"),
                    ("res_id", "=", self.picking.id),
                    ("name", "=", f"DeCA - {self.picking.name} - v1.pdf"),
                ]
            )
            self.assertTrue(att_v1)
            self.assertEqual(att_v1.raw, pdf_1)

            # 2. Second print without changes -> should return exactly the same
            pdf_1_cached, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(
                self.picking.deca_version,
                1,
                "Version should not increment if data did not change.",
            )
            self.assertEqual(
                pdf_1_cached, pdf_1, "Returned PDF should be exactly the same binary."
            )

            # 3. Modify a field not in the hash (e.g. note) -> should still be v1
            self.picking.note = "Test internal note"
            pdf_1_cached_2, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(self.picking.deca_version, 1)

            # 4. Modify a DeCA field -> hash changes -> should generate v2
            self.picking.tractor_license_plate = "9999ZZZ"
            pdf_2, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(
                self.picking.deca_version,
                2,
                "Version should increment because tractor plate changed.",
            )

            # Check v2 attachment
            att_v2 = self.env["ir.attachment"].search(
                [
                    ("res_model", "=", "stock.picking"),
                    ("res_id", "=", self.picking.id),
                    ("name", "=", f"DeCA - {self.picking.name} - v2.pdf"),
                ]
            )
            self.assertTrue(att_v2)

    def test_05_delivery_carrier_form(self):
        """Test delivery carrier form to ensure XML views are fully covered."""
        carrier_form = Form(self.env["delivery.carrier"])
        carrier_form.name = "Test Carrier UI"
        carrier_form.product_id = self.carrier_product
        # Carrier contact should be exposed in the view (in the 'DeCA' group)
        carrier_form.carrier_contact_id = self.carrier_contact
        carrier_record = carrier_form.save()
        self.assertEqual(carrier_record.carrier_contact_id, self.carrier_contact)

    def test_06_stock_picking_form(self):
        """Test stock picking form to ensure XML views are fully covered."""
        picking_form = Form(self.env["stock.picking"])
        picking_form.partner_id = self.partner
        picking_form.picking_type_id = self.picking_type_out
        picking_form.carrier_id = self.carrier
        # Check DeCA fields
        picking_form.tractor_license_plate = "1111AAA"
        picking_form.trailer_license_plate = "R1111BBB"
        picking_form.special_authorization = "AUTH-123"
        # The carrier_contact_id should compute from carrier
        self.assertEqual(picking_form.carrier_contact_id, self.carrier_contact)
        picking_record = picking_form.save()
        self.assertEqual(picking_record.tractor_license_plate, "1111AAA")
