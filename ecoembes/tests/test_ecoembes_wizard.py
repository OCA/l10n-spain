# Copyright 2021-2022 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields
from odoo.tests.common import Form, tagged, users

from .common import TestEcoembesBase


@tagged("post_install", "-at_install")
class TestEcoembesWizard(TestEcoembesBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")
        cls.company.ecoembes_inscription = "REI-RAEE-123456"
        cls.company.ecoembes_partner_member = "ECO-12345"
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner", "country_id": cls.env.ref("base.es").id}
        )
        cls.account_tax = cls.env["account.tax"].create(
            {"name": "0%", "amount_type": "fixed", "type_tax_use": "sale", "amount": 0}
        )
        cls.product_a = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Test Product A",
                    "default_code": "TEST-A",
                    "ecoembes_sig": True,
                    "list_price": 10,
                    "taxes_id": [(6, 0, [cls.account_tax.id])],
                }
            )
        )
        cls.product_b = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Test Product B",
                    "default_code": "TEST-B",
                    "ecoembes_sig": True,
                    "list_price": 10,
                    "taxes_id": [(6, 0, [cls.account_tax.id])],
                }
            )
        )
        cls.product_c = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Test Product C",
                    "default_code": "TEST-C",
                    "list_price": 10,
                    "taxes_id": [(6, 0, [cls.account_tax.id])],
                }
            )
        )
        cls.journal = (
            cls.env["account.journal"]
            .sudo()
            .create({"name": "Test journal sale", "type": "sale", "code": "TEST-SALE"})
        )
        cls.currency = cls.env.ref("base.USD")

    def _create_invoice(self, invoice_date):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="out_invoice",
                default_company_id=self.company.id,
            )
        )
        if not move_form._get_modifier("currency_id", "invisible"):
            move_form.currency_id = self.currency
        if not move_form._get_modifier("invoice_date", "invisible"):
            move_form.invoice_date = invoice_date
        move_form.partner_id = self.partner
        if not move_form._get_modifier("journal_id", "invisible"):
            move_form.journal_id = self.journal
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_a
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_b
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product_c
        return move_form.save()

    @users("ecoembes_manager")
    def test_wizar_get_data(self):
        date = "1990-01-01"
        invoice = self._create_invoice(date)
        self.assertEqual(invoice.invoice_date, fields.Date.from_string("1990-01-01"))
        self.assertEqual(invoice.amount_total, 30)
        self.assertTrue(
            invoice.invoice_line_ids.filtered(lambda x: x.product_id == self.product_a)
        )
        self.assertTrue(
            invoice.invoice_line_ids.filtered(lambda x: x.product_id == self.product_b)
        )
        self.assertTrue(
            invoice.invoice_line_ids.filtered(lambda x: x.product_id == self.product_c)
        )
        item = self.env["ecoembes.sig.report.wizard"].create(
            {"date_start": invoice.invoice_date, "date_end": invoice.invoice_date}
        )
        items = item.get_report_items()
        self.assertEqual(len(items), 0)
        # Post move to get some items
        invoice.action_post()
        items = item.get_report_items()
        self.assertEqual(len(items), 2)
        self.assertTrue(self.product_a in items.mapped("product_id"))
        self.assertTrue(self.product_b in items.mapped("product_id"))
        self.assertEqual(sum(items.mapped("billing")), 20)
        # Example report invoice
        html = self.env["ir.actions.report"]._render_qweb_html(
            "account.report_invoice_with_payments", invoice.ids
        )
        self.assertRegex(str(html[0]), "REI-RAEE-123456")
        self.assertRegex(str(html[0]), "ECO-12345")
