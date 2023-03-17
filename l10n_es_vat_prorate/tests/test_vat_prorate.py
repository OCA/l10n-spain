# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from odoo.tests.common import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVatProrate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(chart_template_ref="l10n_es.account_chart_template_pymes")
        cls.env.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": date(2000, 1, 1), "vat_prorate": 10}),
                    (0, 0, {"date": date(2001, 1, 1), "vat_prorate": 20}),
                ],
            }
        )
        cls.product_b.write(
            {
                "supplier_taxes_id": [(6, 0, cls.tax_purchase_a.ids)],
                "taxes_id": [(6, 0, cls.tax_sale_a.ids)],
            }
        )
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {"name": "Test analytic account"}
        )

    def test_no_prorate_in_invoice(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_different_accounts_in_invoice(self):
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(3, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        # Deal with analytics
        with Form(invoice) as invoice_form:
            with invoice_form.invoice_line_ids.edit(0) as line_form:
                line_form.analytic_account_id = self.analytic_account
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(
            1,
            len(
                invoice.line_ids.filtered(
                    lambda r: r.tax_line_id and r.analytic_account_id
                )
            ),
        )

    def test_prorate_same_accounts_in_invoice(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_expense"
        ]
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_no_prorate_in_refund(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_different_accounts_in_refund(self):
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(3, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_same_accounts_in_refund(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_expense"
        ]
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_no_prorate_out_invoice(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "out_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_out_invoice(self):
        invoice = self.init_invoice(
            "out_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_no_prorate_out_refund(self):
        self.env.company.write(
            {"with_vat_prorate": False}
        )  # We want to be sure that it is executed properly
        invoice = self.init_invoice(
            "out_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_out_refund(self):
        invoice = self.init_invoice(
            "out_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
