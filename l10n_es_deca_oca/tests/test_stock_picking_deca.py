# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
from unittest.mock import patch

from pypdf import PdfWriter

from odoo.exceptions import UserError
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
                "vat": "ES12345678Z",
            }
        )

        # Create carrier contact
        cls.carrier_contact = cls.env["res.partner"].create(
            {
                "name": "Carrier Contact",
                "vat": "ES87654321X",
            }
        )

        # Create product and stock location for picking
        cls.product = cls.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "weight": 2.5,
            }
        )

        cls.location_customer = cls.env.ref("stock.stock_location_customers")
        cls.location_stock = cls.env.ref("stock.stock_location_stock")
        cls.picking_type_out = cls.env.ref("stock.picking_type_out")

        # Create a picking
        cls.env.company.vat = "ESB12345678"
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.partner.id,
                "picking_type_id": cls.picking_type_out.id,
                "location_id": cls.location_stock.id,
                "location_dest_id": cls.location_customer.id,
                "tractor_license_plate": "1111AAA",
                "trailer_license_plate": "R1111BBB",
                "special_authorization": "AUTH-123",
                "carrier_contact_id": cls.carrier_contact.id,
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

            # 5. Modify trailer plate -> should generate v3
            self.picking.trailer_license_plate = "R9999XXX"
            pdf_3, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(
                self.picking.deca_version,
                3,
                "Version should increment because trailer plate changed.",
            )

            # 6. Modify special authorization -> should generate v4
            self.picking.special_authorization = "NEW-AUTH"
            pdf_4, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(
                self.picking.deca_version,
                4,
                "Version should increment because special authorization changed.",
            )

            # 7. Modify carrier contact -> should generate v5
            new_carrier = self.env["res.partner"].create(
                {"name": "New Carrier", "vat": "ES99999999R"}
            )
            self.picking.carrier_contact_id = new_carrier
            pdf_5, _ext = report._render_qweb_pdf(
                "l10n_es_deca_oca.report_deca", [self.picking.id]
            )
            self.assertEqual(
                self.picking.deca_version,
                5,
                "Version should increment because carrier contact changed.",
            )

    def test_06_stock_picking_form(self):
        """Test stock picking form to ensure XML views are fully covered."""
        picking_form = Form(self.env["stock.picking"])
        picking_form.partner_id = self.partner
        picking_form.picking_type_id = self.picking_type_out
        # Check DeCA fields
        picking_form.tractor_license_plate = "1111AAA"
        picking_form.trailer_license_plate = "R1111BBB"
        picking_form.special_authorization = "AUTH-123"
        picking_form.carrier_contact_id = self.carrier_contact

        picking_record = picking_form.save()
        self.assertEqual(picking_record.tractor_license_plate, "1111AAA")
        self.assertEqual(picking_record.carrier_contact_id, self.carrier_contact)

    def test_07_render_report(self):
        """Test rendering the report HTML to ensure QWeb template parses correctly."""
        report = self.env["ir.actions.report"]._get_report_from_name(
            "l10n_es_deca_oca.report_deca"
        )

        # 1. Picking Out with Carrier Contact
        html, _ext = report._render_qweb_html(report.report_name, self.picking.ids)
        self.assertIn(b"Document for electronic Control of Administration (DeCA)", html)
        self.assertIn(b"Carrier Contact", html)

        # 2. Picking In without Carrier Contact
        picking_in = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.location_customer.id,
                "location_dest_id": self.location_stock.id,
                "tractor_license_plate": "2222BBB",
                "carrier_contact_id": self.carrier_contact.id,
            }
        )
        self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_in.id,
                "location_id": self.location_customer.id,
                "location_dest_id": self.location_stock.id,
            }
        )
        html_in, _ext = report._render_qweb_html(report.report_name, picking_in.ids)
        self.assertIn(
            b"Document for electronic Control of Administration (DeCA)", html_in
        )

        # 3. Picking Internal
        picking_int = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_internal").id,
                "location_id": self.location_stock.id,
                "location_dest_id": self.location_stock.id,
                "tractor_license_plate": "3333CCC",
                "carrier_contact_id": self.carrier_contact.id,
            }
        )
        self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": 2.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_int.id,
                "location_id": self.location_stock.id,
                "location_dest_id": self.location_stock.id,
            }
        )
        html_int, _ext = report._render_qweb_html(report.report_name, picking_int.ids)
        self.assertIn(
            b"Document for electronic Control of Administration (DeCA)", html_int
        )

    def test_08_weight_computation_and_view(self):
        """Test weight computations on move and picking."""
        # The move has 10 units and product weight is 2.5
        # Force recompute by writing to a dependent field
        self.move.product_uom_qty = 10.0
        self.assertEqual(self.move.deca_weight, 25.0)
        self.assertEqual(self.picking.deca_weight, 25.0)

        # Modify quantity and check if weight updates
        self.move.product_uom_qty = 5.0
        self.assertEqual(self.move.deca_weight, 12.5)
        self.assertEqual(self.picking.deca_weight, 12.5)

    def test_09_check_deca_required_fields(self):
        """Test the required fields validation for DeCA report."""
        self.env.company.partner_id.vat = "ESB12345678"

        # 1. Missing tractor_license_plate
        self.picking.tractor_license_plate = False
        with self.assertRaises(UserError) as e:
            self.picking._check_deca_required_fields()
        self.assertIn("Main vehicle or tractor licence plate", str(e.exception))
        self.picking.tractor_license_plate = "1111AAA"

        # 2. Missing carrier contact
        self.picking.carrier_contact_id = False
        with self.assertRaises(UserError) as e:
            self.picking._check_deca_required_fields()
        self.assertIn("Carrier contact", str(e.exception))
        self.picking.carrier_contact_id = self.carrier_contact

        # 3. Missing carrier VAT
        self.picking.carrier_contact_id.vat = False
        with self.assertRaises(UserError) as e:
            self.picking._check_deca_required_fields()
        self.assertIn("Carrier NIF (VAT)", str(e.exception))
        self.picking.carrier_contact_id.vat = "ES87654321X"

        # 4. Missing partner VAT
        self.picking.partner_id.vat = False
        with self.assertRaises(UserError) as e:
            self.picking._check_deca_required_fields()
        self.assertIn("Consignee NIF (VAT)", str(e.exception))
        self.picking.partner_id.vat = "ES12345678Z"

        # 5. Missing sender VAT
        self.env.company.partner_id.vat = False
        with self.assertRaises(UserError) as e:
            self.picking._check_deca_required_fields()
        self.assertIn("Sender NIF (VAT)", str(e.exception))
        self.env.company.partner_id.vat = "ESB12345678"

        # 6. Missing weight
        self.move.product_uom_qty = 0
        self.assertEqual(self.picking.deca_weight, 0.0)
        with self.assertRaises(UserError) as e:
            self.picking._check_deca_required_fields()
        self.assertIn("Weight", str(e.exception))

    def test_10_action_get_share_url(self):
        """Test action_get_share_url returns correct action dict."""
        action = self.picking.action_get_share_url()
        self.assertEqual(action.get("type"), "ir.actions.act_url")
        self.assertEqual(action.get("target"), "new")
        self.assertTrue(action.get("url").startswith(self.picking._get_share_url()))

    def test_11_incoming_picking_deca_enabled(self):
        """Test l10n_es_show_deca field logic for incoming and outgoing pickings."""
        # By default, outgoing is always True
        self.assertTrue(self.picking.l10n_es_show_deca)

        picking_in = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.location_customer.id,
                "location_dest_id": self.location_stock.id,
            }
        )

        # By default, incoming is False because picking_type has enabled = False
        self.assertFalse(picking_in.l10n_es_show_deca)

        # Enable DeCA for incoming picking type
        picking_in.picking_type_id.l10n_es_deca_enabled = True

        # Now it should be True
        self.assertTrue(picking_in.l10n_es_show_deca)

    def test_12_incoming_picking_required_fields(self):
        """Test DeCA required fields validation for incoming pickings."""
        self.env.company.partner_id.vat = "ESB12345678"
        self.partner.vat = "ES12345678Z"

        picking_in = self.env["stock.picking"].create(
            {
                "partner_id": self.partner.id,
                "picking_type_id": self.env.ref("stock.picking_type_in").id,
                "location_id": self.location_customer.id,
                "location_dest_id": self.location_stock.id,
                "tractor_license_plate": "2222BBB",
                "carrier_contact_id": self.carrier_contact.id,
            }
        )
        self.env["stock.move"].create(
            {
                "product_id": self.product.id,
                "product_uom_qty": 5.0,
                "product_uom": self.product.uom_id.id,
                "picking_id": picking_in.id,
                "location_id": self.location_customer.id,
                "location_dest_id": self.location_stock.id,
            }
        )

        # 1. Missing sender VAT (the partner/supplier)
        picking_in.partner_id.vat = False
        with self.assertRaises(UserError) as e:
            picking_in._check_deca_required_fields()
        self.assertIn("Sender NIF (VAT)", str(e.exception))
        picking_in.partner_id.vat = "ES12345678Z"

        # 2. Missing consignee VAT (the company)
        self.env.company.partner_id.vat = False
        with self.assertRaises(UserError) as e:
            picking_in._check_deca_required_fields()
        self.assertIn("Consignee NIF (VAT)", str(e.exception))
        self.env.company.partner_id.vat = "ESB12345678"
