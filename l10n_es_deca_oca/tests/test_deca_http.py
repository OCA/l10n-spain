# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlsplit

import pytz

from odoo import fields
from odoo.tests import tagged
from odoo.tests.common import HttpCase, save_test_file
from odoo.tools.pdf import PdfFileReader

from .common import DecaCommon


@tagged("post_install", "-at_install")
class TestDecaHttp(DecaCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Assets must be fetched from this rollback-enabled runner, not the stopped
        # development service. This is test infrastructure, not a PDF mock.
        cls.env["ir.config_parameter"].set_param("report.url", cls.base_url())

    def test_company_timezone_dates_and_public_cache(self):
        self.company.partner_id.tz = "Europe/Madrid"
        self.stock_user.tz = "America/Los_Angeles"
        public_user = self.env.ref("base.public_user")
        public_user.tz = "Asia/Tokyo"
        issued = fields.Datetime.now().replace(
            hour=23, minute=30, second=0, microsecond=0
        )
        loading = issued + timedelta(days=2)
        done = issued + timedelta(days=3)
        # Log-access fields cannot be changed by write() after registry loading.
        # Fix only the creation clock; the report still reads the persisted date.
        with patch.object(self.cr, "now", return_value=issued):
            self.picking = self._make_picking()
            self.env.flush_all()
        self.assertEqual(self.picking.create_date, issued)
        self.picking.scheduled_date = loading
        company_zone = pytz.timezone("Europe/Madrid")

        def expected_date(timestamp):
            return (
                pytz.utc.localize(timestamp)
                .astimezone(company_zone)
                .strftime("%d/%m/%Y")
            )

        stock_picking = self.picking.with_user(self.stock_user)
        public_picking = self.picking.with_user(public_user).sudo()
        self.assertNotEqual(expected_date(issued), issued.strftime("%d/%m/%Y"))
        for picking in (stock_picking, public_picking):
            values = picking._get_deca_report_data()
            self.assertEqual(values["issue_date"], expected_date(issued))
            self.assertEqual(values["loading_date"], expected_date(loading))
        self.assertEqual(
            stock_picking._get_deca_hash(), public_picking._get_deca_hash()
        )
        self.picking.date_done = done
        for picking in (stock_picking, public_picking):
            values = picking._get_deca_report_data()
            self.assertEqual(values["issue_date"], expected_date(issued))
            self.assertEqual(values["loading_date"], expected_date(done))
        content, kind = (
            self.env["ir.actions.report"]
            .with_user(self.stock_user)
            ._render_qweb_pdf("l10n_es_deca_oca.report_deca", self.picking.ids)
        )
        self.assertEqual(kind, "pdf")
        self.assertTrue(content.startswith(b"%PDF"))
        version_hash = self.picking.deca_content_hash
        current_file = self.picking.deca_attachment_id
        self.assertEqual(self.picking.deca_version, 1)
        self.assertEqual(public_picking._get_deca_hash(), version_hash)
        public_pdf, _kind = (
            self.env["ir.actions.report"]
            .with_user(public_user)
            .sudo()
            ._render_qweb_pdf("l10n_es_deca_oca.report_deca", self.picking.ids)
        )
        self.assertEqual(public_pdf, content)
        self.authenticate(None, None)
        url = urlsplit(stock_picking.action_get_share_url()["url"])
        self.env.flush_all()
        response = self.url_open(url.path + "?" + url.query, timeout=60)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, content)
        self.picking.invalidate_recordset()
        self.assertEqual(self.picking.deca_version, 1)
        self.assertEqual(self.picking.deca_content_hash, version_hash)
        self.assertEqual(self.picking.deca_attachment_id, current_file)
        self.assertEqual(current_file.raw, content)

    def test_corrected_grams_pdf(self):
        gram = self.env.ref("uom.product_uom_gram")
        self.env["ir.config_parameter"].set_param(
            "product_default_weight_uom_id", gram.id
        )
        with patch.object(
            type(self.env["product.template"]),
            "_get_weight_uom_id_from_ir_config_parameter",
            return_value=gram,
        ):
            self.move.product_uom_qty = 1
            self.assertAlmostEqual(self.picking.deca_weight, 0.0025, places=9)
            self.move.product_uom_qty = 10
            self.assertAlmostEqual(self.picking.deca_weight, 0.025, places=9)
            content, kind = self._pdf()
            self.assertEqual(kind, "pdf")
            self.assertTrue(content.startswith(b"%PDF"))
            save_test_file(
                "deca_corrected_grams",
                content,
                "deca_",
                extension="pdf",
                document_type="Corrected grams DeCA PDF",
            )

    def test_public_token_scope_and_live_validation(self):
        self.authenticate(None, None)
        url = urlsplit(self.picking.action_get_share_url()["url"])
        route = url.path + "?" + url.query
        other = self._make_picking()
        other.action_get_share_url()
        # Render the real PDF outside the HTTP transaction. HttpCase serializes
        # request cursors, so wkhtmltopdf's nested asset requests otherwise deadlock.
        # The coordinator checks first issuance over HTTP without test-mode locks.
        expected_pdf, _kind = self._pdf()
        save_test_file(
            "deca_pdf", expected_pdf, "deca_", extension="pdf", document_type="DeCA PDF"
        )
        self.env.flush_all()
        for denied in (
            url.path,
            url.path + "?access_token=invalid",
            url.path + "?access_token=" + other.deca_access_token,
            "/my/picking/2147483647?" + url.query,
        ):
            response = self.url_open(denied)
            self.assertEqual(response.status_code, 404)
            self.assertEqual(response.content, b"Not Found")

        response = self.url_open(route, timeout=60)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["Content-Type"], "application/pdf")
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertTrue(response.content.startswith(b"%PDF"))
        self.assertEqual(response.content, expected_pdf)
        self.assertGreater(PdfFileReader(io.BytesIO(response.content)).getNumPages(), 0)
        self.picking.invalidate_recordset()
        original = self.picking.deca_attachment_id
        self.assertEqual(original.raw, response.content)
        self.assertEqual(self.url_open(route).content, response.content)
        self.assertEqual(self.picking.deca_version, 1)
        arbitrary = self.env["ir.attachment"].create(
            {
                "name": "private.txt",
                "raw": b"unrelated private content",
                "res_model": "stock.picking",
                "res_id": self.picking.id,
            }
        )
        self.env.flush_all()
        self.assertEqual(
            self.url_open(route + f"&attachment_id={arbitrary.id}").content,
            response.content,
        )
        self.assertNotEqual(
            self.url_open(
                f"/web/content/{arbitrary.id}?download=true&{url.query}"
            ).status_code,
            200,
        )
        self.assertNotEqual(
            self.url_open(
                f"/web/content/{original.id}?download=true&{url.query}"
            ).status_code,
            200,
        )
        self.carrier_contact.vat = False
        self.env.flush_all()
        invalid = self.url_open(route)
        self.assertEqual(invalid.status_code, 404)
        self.assertEqual(invalid.content, b"Not Found")
        self.assertEqual(original.raw, response.content)
        self.picking.invalidate_recordset()
        self.assertEqual(self.picking.deca_version, 1)
