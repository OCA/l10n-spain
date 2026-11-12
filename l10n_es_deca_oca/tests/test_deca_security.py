# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from psycopg2 import IntegrityError

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import HttpCase
from odoo.tools import mute_logger

from .common import DecaCommon


@tagged("post_install", "-at_install")
class TestDecaSecurity(DecaCommon, HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Share rollback fixtures with wkhtmltopdf asset requests on the test server.
        cls.env["ir.config_parameter"].set_param("report.url", cls.base_url())

    def test_issued_file_immutable(self):
        self._pdf()
        attachment = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "stock.picking"),
                ("res_id", "=", self.picking.id),
                ("name", "=", f"DeCA - {self.picking.name} - v1.pdf"),
            ]
        )
        with self.assertRaises(AccessError):
            attachment.with_user(self.stock_user).write({"raw": b"forged"})
        with self.assertRaises(AccessError):
            attachment.sudo().unlink()

    def test_provenance_and_generation_fields(self):
        picking = self.picking.with_user(self.stock_user)
        for values in (
            {"deca_version": 1},
            {"deca_content_hash": "forged"},
            {"deca_attachment_id": False},
            {"deca_first_version_date": False},
            {"tractor_license_plate_history": "forged"},
        ):
            with self.subTest(values=values), self.assertRaises(AccessError):
                picking.with_context(deca_generation=True).write(values)
        with self.assertRaises(AccessError):
            picking.with_context(default_deca_access_token="forged").copy()
        for values in (
            {"deca_source_id": picking.id},
            {"deca_version": 1},
            {"deca_content_hash": "x"},
        ):
            with self.subTest(values=values), self.assertRaises(AccessError):
                self.env["ir.attachment"].with_user(self.stock_user).create(
                    {"name": "fake.pdf", **values}
                )
        with self.assertRaises(AccessError):
            self.env["ir.attachment"].with_user(self.stock_user).with_context(
                default_deca_source_id=picking.id
            ).create({"name": "fake.pdf"})
        self.assertNotIn(
            "deca_access_token",
            self.env["stock.picking"].with_user(self.internal_user).fields_get(),
        )
        with self.assertRaises(AccessError):
            self.env["ir.actions.report"].with_user(
                self.internal_user
            )._render_qweb_pdf("l10n_es_deca_oca.report_deca", picking.ids)

    def test_file_versions_cannot_be_replaced_or_moved(self):
        fake = (
            self.env["ir.attachment"]
            .with_user(self.stock_user)
            .create(
                {
                    "name": f"DeCA - {self.picking.name} - v1.pdf",
                    "raw": b"forged PDF",
                    "res_model": "stock.picking",
                    "res_id": self.picking.id,
                }
            )
        )
        first_pdf, _kind = self._pdf()
        issued = self.picking.deca_attachment_id
        self.assertNotEqual(fake, issued)
        self.assertNotEqual(first_pdf, fake.raw)
        self.picking.tractor_license_plate = "2222BBB"
        self._pdf()
        for file in issued | self.picking.deca_attachment_id:
            for values in (
                {"name": "changed.pdf"},
                {"res_id": False},
                {"res_model": "res.partner"},
                {"public": True},
                {"access_token": "forged"},
                {"deca_source_id": False},
            ):
                with self.subTest(values=values), self.assertRaises(AccessError):
                    file.with_user(self.stock_user).write(values)
            with self.assertRaises(AccessError):
                file.with_user(self.stock_user).unlink()
        self.assertEqual(issued.raw, first_pdf)
        fake.write({"raw": b"ordinary files stay editable", "name": "unrelated.txt"})
        fake.unlink()
        self.assertFalse(fake.exists())

    def test_native_picking_deletion_and_backorder(self):
        for cancelled in (False, True):
            picking = self._make_picking()
            self._pdf(picking)
            file = picking.deca_attachment_id
            if cancelled:
                picking.action_cancel()
            picking.unlink()
            self.assertFalse(picking.exists())
            self.assertFalse(file.exists())
        self.picking.action_confirm()
        self.move.quantity = 4
        self.move.picked = True
        self.picking.with_context(
            skip_backorder=True, picking_ids_not_to_backorder=[]
        ).button_validate()
        self.assertEqual(self.picking.state, "done")
        backorder = self.env["stock.picking"].search(
            [("backorder_id", "=", self.picking.id)]
        )
        self.assertTrue(backorder)
        self.picking.action_get_share_url()
        backorder.action_get_share_url()
        self.assertNotEqual(self.picking.deca_access_token, backorder.deca_access_token)
        self._pdf()
        with self.assertRaises(UserError):
            self.picking.unlink()
        self.assertTrue(self.picking.deca_attachment_id.exists())

    def test_company_isolation(self):
        other_company = self.env["res.company"].create(
            {"name": "DECA Restricted Company"}
        )
        foreign_carrier = self.env["res.partner"].create(
            {"name": "Foreign carrier", "company_id": other_company.id}
        )
        with self.assertRaises(UserError):
            self.picking.carrier_contact_id = foreign_carrier
        self._pdf()
        self.assertEqual(self.picking.deca_attachment_id.company_id, self.company)
        self.stock_user.write(
            {"company_ids": [(6, 0, other_company.ids)], "company_id": other_company.id}
        )
        restricted = self.picking.with_user(self.stock_user).with_context(
            allowed_company_ids=other_company.ids
        )
        with self.assertRaises(AccessError):
            restricted.action_get_share_url()
        with self.assertRaises(AccessError):
            self.env["ir.actions.report"].with_user(self.stock_user).with_context(
                allowed_company_ids=other_company.ids
            )._render_qweb_pdf("l10n_es_deca_oca.report_deca", self.picking.ids)
        with self.assertRaises(AccessError):
            restricted.read(["deca_attachment_id"])

    def test_unique_version_constraint(self):
        self._pdf()
        current = self.picking.deca_attachment_id
        with (
            mute_logger("odoo.sql_db"),
            self.assertRaises(IntegrityError),
            self.cr.savepoint(),
        ):
            self.env["ir.attachment"].create(
                {
                    "name": "duplicate.pdf",
                    "raw": current.raw,
                    "mimetype": "application/pdf",
                    "res_model": "stock.picking",
                    "res_id": self.picking.id,
                    "company_id": self.company.id,
                    "deca_source_id": self.picking.id,
                    "deca_version": current.deca_version,
                    "deca_content_hash": current.deca_content_hash,
                }
            )
        self.assertEqual(
            self.env["ir.attachment"].search_count(
                [("deca_source_id", "=", self.picking.id)]
            ),
            1,
        )

    def test_inventory_user_can_issue(self):
        content, kind = (
            self.env["ir.actions.report"]
            .with_user(self.stock_user)
            ._render_qweb_pdf("l10n_es_deca_oca.report_deca", self.picking.ids)
        )
        self.assertEqual(kind, "pdf")
        self.assertTrue(content.startswith(b"%PDF"))
        self.assertEqual(self.picking.deca_version, 1)
        self.assertEqual(self.picking.deca_attachment_id.raw, content)

    def test_token_copy_and_forgery(self):
        picking = self.picking.with_user(self.stock_user)
        picking.action_get_share_url()
        self.assertTrue(picking.deca_access_token)
        duplicate = picking.copy()
        self.assertFalse(duplicate.deca_access_token)
        duplicate.action_get_share_url()
        self.assertNotEqual(duplicate.deca_access_token, picking.deca_access_token)
        with self.assertRaises(AccessError):
            picking.write({"deca_access_token": "forged-token"})
        with self.assertRaises(AccessError):
            picking.with_context(deca_generation=True).write({"deca_version": 99})
        with self.assertRaises(AccessError):
            self.picking.with_user(self.internal_user).action_get_share_url()
