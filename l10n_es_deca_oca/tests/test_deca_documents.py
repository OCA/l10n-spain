# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import io
from datetime import timedelta

import pytz
from lxml import html

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import HttpCase
from odoo.tools.pdf import PdfFileReader

from .common import DecaCommon


@tagged("post_install", "-at_install")
class TestDecaDocuments(DecaCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env["ir.config_parameter"].set_param("report.url", cls.base_url())

    def test_scalar_list_multiple_and_order(self):
        report = self.env["ir.actions.report"].with_context(force_report_rendering=True)
        ref = "l10n_es_deca_oca.report_deca"
        first, _kind = report._render_qweb_pdf(ref, self.picking.id)
        self.assertEqual(report._render_qweb_pdf(ref, self.picking.ids)[0], first)
        other = self._make_picking(incoming=True)
        other.tractor_license_plate = "9999ZZZ"
        second, _kind = self._pdf(other)
        merged, kind = report._render_qweb_pdf(ref, [other.id, self.picking.id])
        self.assertEqual(kind, "pdf")
        expected = [PdfFileReader(io.BytesIO(content)) for content in (second, first)]
        actual = PdfFileReader(io.BytesIO(merged))
        pages = [
            reader.getPage(i)
            for reader in expected
            for i in range(reader.getNumPages())
        ]
        self.assertEqual(actual.getNumPages(), len(pages))
        for index, page in enumerate(pages):
            self.assertEqual(
                actual.getPage(index).getContents().getData(),
                page.getContents().getData(),
            )
        self.assertEqual(self.picking.deca_version, 1)
        self.assertEqual(other.deca_version, 1)
        self.assertEqual(self.picking.deca_attachment_id.raw, first)
        self.assertEqual(other.deca_attachment_id.raw, second)

    def test_direction_dates_goods_and_qr(self):
        self.company.partner_id.write(
            {"street": "Loading Warehouse 12", "tz": "Europe/Madrid"}
        )
        company_zone = pytz.timezone("Europe/Madrid")
        loading_date = fields.Datetime.now().replace(
            hour=12, minute=0, second=0, microsecond=0
        ) + timedelta(days=2)
        for incoming in (False, True):
            picking = self._make_picking(incoming=incoming)
            picking.scheduled_date = loading_date
            report_html, _kind = self.env["ir.actions.report"]._render_qweb_html(
                "l10n_es_deca_oca.report_deca", picking.ids
            )
            tree = html.fromstring(report_html)
            sender = tree.xpath("//strong[contains(., 'Sender /')]/..")[
                0
            ].text_content()
            consignee = tree.xpath("//strong[contains(., 'Consignee /')]/..")[
                0
            ].text_content()
            self.assertIn(
                "Customer Street 10" if incoming else "Loading Warehouse 12", sender
            )
            self.assertIn(
                "Loading Warehouse 12" if incoming else "Customer Street 10", consignee
            )
            for timestamp in (picking.create_date, loading_date):
                expected_date = (
                    pytz.utc.localize(timestamp)
                    .astimezone(company_zone)
                    .strftime("%d/%m/%Y")
                )
                self.assertIn(expected_date, tree.text_content())
            self.assertIn("DECA Test Cargo", tree.text_content())
            self.assertTrue(
                tree.xpath("//img[starts-with(@src, 'data:image/png;base64,')]")
            )
            self.assertIn("25.00", tree.text_content().replace(",", "."))
            # Upstream prints actual quantity, but uses planned weight when zero.
            self.assertEqual(picking.move_ids.quantity, 0)
            self.assertEqual(picking.deca_weight, 25)
        cancelled = self.move.copy(
            {"picking_id": self.picking.id, "product_uom_qty": 2}
        )
        cancelled._action_cancel()
        self.assertEqual(self.picking.deca_weight, 25)
        self.assertEqual(len(self.picking._get_deca_report_data()["goods"]), 2)

    def test_changed_invalid_data_never_returns_stale_pdf(self):
        first, _kind = self._pdf()
        file = self.picking.deca_attachment_id
        self.carrier_contact.vat = False
        with self.assertRaises(UserError):
            self._pdf()
        self.assertEqual(file.raw, first)
        self.assertEqual(self.picking.deca_version, 1)

    def test_hash_includes_printed_data_not_timestamps(self):
        before = self.picking._get_deca_hash()
        self.picking.note = "Non-printed note"
        self.assertEqual(self.picking._get_deca_hash(), before)
        for record, field, value in (
            (self.partner, "street", "New customer address"),
            (self.company.partner_id, "street", "New warehouse address"),
            (self.product, "name", "New cargo name"),
            (self.company, "report_footer", "New footer"),
            (self.picking, "tractor_license_plate", "5555DDD"),
        ):
            record[field] = value
            after = self.picking._get_deca_hash()
            self.assertNotEqual(before, after)
            before = after

    def test_inventory_compiled_views_and_help(self):
        model = self.env["stock.picking"].with_user(self.stock_user)
        view = model.get_view(self.env.ref("stock.view_picking_form").id, "form")
        tree = html.fromstring(view["arch"])
        self.assertTrue(tree.xpath("//button[@name='action_get_share_url']"))
        self.assertTrue(tree.xpath("//page[@name='deca_info']"))
        metadata = model.fields_get()
        for field in (
            "tractor_license_plate",
            "trailer_license_plate",
            "special_authorization",
            "carrier_contact_id",
            "deca_weight",
            "deca_version",
        ):
            self.assertTrue(metadata[field].get("help"), field)
        self.assertTrue(
            self.env["stock.picking.type"].fields_get()["l10n_es_deca_enabled"]["help"]
        )
