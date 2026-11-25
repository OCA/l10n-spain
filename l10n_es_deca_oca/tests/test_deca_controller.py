# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
from unittest.mock import patch

from pypdf import PdfWriter

from odoo.tests import HttpCase, tagged

from odoo.addons.base.models.ir_actions_report import IrActionsReport


@tagged("post_install", "-at_install")
class TestDecaController(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.partner_id.vat = "ESB12345674"
        partner = cls.env["res.partner"].create(
            {"name": "Test Partner", "vat": "ES12345678Z"}
        )
        carrier = cls.env["res.partner"].create(
            {"name": "Carrier Contact", "vat": "ES87654321X"}
        )
        product = cls.env["product.product"].create(
            {"name": "Test Product", "type": "consu", "weight": 2.5}
        )
        location_stock = cls.env.ref("stock.stock_location_stock")
        location_customer = cls.env.ref("stock.stock_location_customers")
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": partner.id,
                "picking_type_id": cls.env.ref("stock.picking_type_out").id,
                "location_id": location_stock.id,
                "location_dest_id": location_customer.id,
                "tractor_license_plate": "1111AAA",
                "carrier_contact_id": carrier.id,
            }
        )
        cls.env["stock.move"].create(
            {
                "product_id": product.id,
                "product_uom_qty": 10.0,
                "uom_id": product.uom_id.id,
                "picking_id": cls.picking.id,
                "location_id": location_stock.id,
                "location_dest_id": location_customer.id,
            }
        )
        writer = PdfWriter()
        writer.add_blank_page(width=72, height=72)
        out = io.BytesIO()
        writer.write(out)
        cls.dummy_pdf = out.getvalue()

    def test_01_not_found(self):
        """Invalid requests return 404."""
        self.picking._get_share_url()
        token = self.picking.deca_access_token
        urls = [
            # No picking id
            f"/my/picking/0?access_token={token}",
            # Picking does not exist
            f"/my/picking/{self.picking.id + 1000000}?access_token={token}",
            # No access token
            f"/my/picking/{self.picking.id}",
            # Wrong access token
            f"/my/picking/{self.picking.id}?access_token=wrong",
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.url_open(url)
                self.assertEqual(response.status_code, 404)

    def test_02_not_found_without_token_on_picking(self):
        """A picking that was never shared can not be downloaded."""
        self.assertFalse(self.picking.deca_access_token)
        response = self.url_open(f"/my/picking/{self.picking.id}?access_token=x")
        self.assertEqual(response.status_code, 404)

    def test_03_download_pdf(self):
        """A valid token downloads the DeCA PDF."""
        url = self.picking._get_share_url()
        path = url[url.index("/my/picking/") :]
        with patch.object(
            IrActionsReport,
            "_render_qweb_pdf",
            return_value=(self.dummy_pdf, "pdf"),
        ):
            response = self.url_open(path)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertIn(
            f'filename="DeCA - {self.picking.name}.pdf"',
            response.headers["Content-Disposition"],
        )
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertEqual(self.picking.deca_version, 1)
