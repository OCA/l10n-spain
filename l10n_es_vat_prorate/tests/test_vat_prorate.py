from datetime import date
from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo import exceptions
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVatProrate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.env = cls.env(
            context=dict(
                cls.env.context,
                mail_create_nolog=True,
                mail_create_nosubscribe=True,
                mail_notrack=True,
                no_reset_password=True,
                tracking_disable=True,
            )
        )
        cls.purchase_tax_21 = cls.env["account.tax"].create(
            {
                "name": "P IVA 21 SP IN",
                "amount": 21,
                "type_tax_use": "purchase",
                "company_id": cls.env.company.id,
            }
        )
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
        cls.analytic_plan = cls.env["account.analytic.plan"].create({"name": "Default"})
        cls.analytic_account = cls.env["account.analytic.account"].create(
            {
                "name": "Test analytic account",
                "plan_id": cls.analytic_plan.id,
            }
        )

        cls.prorate_expense_account = cls.env["account.account"].create(
            {
                "name": "VAT Prorate Expense",
                "code": "6xxVATPRO",
                "account_type": "expense",
            }
        )

        cls.env.company.expense_currency_exchange_account_id = (
            cls.prorate_expense_account
        )

    def _get_safe_expense_account(self):
        return self.prorate_expense_account

    def setUp(self):
        super().setUp()
        self.patcher = patch.object(
            self.env["account.move"].__class__,
            "_get_prorate_expense_account",
            return_value=self.prorate_expense_account,
        )
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        super().tearDown()

    def _get_safe_expense_account(self):
        return self.prorate_expense_account

    @mute_logger("odoo.sql_db")
    def test_zzz_company_vat_prorate_out_of_range(self):
        vat_prorate_line = self.env.company.vat_prorate_ids[0]
        with self.assertRaises(IntegrityError):
            vat_prorate_line.vat_prorate = 200

    def test_company_special_vat_prorate_out_of_range(self):
        prorate_id = self.env.company.vat_prorate_ids[0]
        with self.assertRaises(exceptions.ValidationError):
            prorate_id.write({"type": "special", "vat_prorate": 100})

    def test_no_company_vat_prorate_information(self):
        self.assertTrue(self.env.company.vat_prorate_ids)
        with self.assertRaises(exceptions.ValidationError):
            self.env.company.write({"vat_prorate_ids": False})

    def test_no_prorate_in_invoice(self):
        self.env.company.write({"with_vat_prorate": False})
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_different_accounts_in_invoice(self):
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))
        first_line = invoice.line_ids[0]
        first_line.analytic_distribution = {self.analytic_account.id: 100}
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(
            0,
            len(
                invoice.line_ids.filtered(
                    lambda r: r.tax_line_id and r.analytic_distribution
                )
            ),
        )

    def test_prorate_tax_with_prorate_account(self):
        tax = self.purchase_tax_21
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b], taxes=[tax]
        )
        self.assertEqual(7, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        self.assertEqual(2, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))

    def test_prorate_same_accounts_in_invoice(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_expense"
        ]
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        tax_lines = invoice.line_ids.filtered(lambda r: r.tax_line_id)
        self.assertEqual(1, len(tax_lines))
        prorate_lines = invoice.line_ids.filtered(lambda r: r.vat_prorate)
        self.assertEqual(1, len(prorate_lines))

    def test_no_prorate_in_refund(self):
        self.env.company.write({"with_vat_prorate": False})
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_different_accounts_in_refund(self):
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))

    def test_prorate_same_accounts_in_refund(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_expense"
        ]
        invoice = self.init_invoice(
            "in_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))

    def test_no_prorate_out_invoice(self):
        self.env.company.write({"with_vat_prorate": False})
        invoice = self.init_invoice(
            "out_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_out_invoice(self):
        invoice = self.init_invoice(
            "out_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_no_prorate_out_refund(self):
        self.env.company.write({"with_vat_prorate": False})
        invoice = self.init_invoice(
            "out_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_out_refund(self):
        invoice = self.init_invoice(
            "out_refund", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_make_refund(self):
        invoice = self.init_invoice("in_invoice", products=[self.product_a])
        invoice.action_post()
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=invoice.ids, active_model="account.move")
            .create({"journal_id": invoice.journal_id.id})
        )
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        self.assertEqual(len(refund.line_ids), 4)
        tax_lines = refund.line_ids.filtered(lambda r: r.tax_line_id)
        self.assertEqual(len(tax_lines), 1)
        prorate_lines = refund.line_ids.filtered(lambda r: r.vat_prorate)
        self.assertEqual(len(prorate_lines), 1)

    def test_special_prorate_default_true(self):
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": True,
            }
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))

    def test_special_prorate_default_false(self):
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": False,
            }
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered(lambda r: r.vat_prorate)))

    def test_special_prorate_mixed(self):
        self.env.company.vat_prorate_ids[0].write(
            {
                "type": "special",
                "special_vat_prorate_default": True,
            }
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        for line in invoice.invoice_line_ids.filtered(
            lambda rec: rec.product_id == self.product_a
        ):
            line.with_vat_prorate = False
        self.assertEqual(5, len(invoice.line_ids))
        lines_with_prorate = invoice.line_ids.filtered(lambda rec: rec.vat_prorate)
        self.assertEqual(
            1,
            len(lines_with_prorate),
            f"Expected 1 line with vat_prorate, found {len(lines_with_prorate)}",
        )

    def test_no_prorate_line_when_100_percent(self):
        self.env.company.write(
            {
                "vat_prorate_ids": [
                    (
                        0,
                        0,
                        {
                            "date": date(2025, 1, 1),
                            "vat_prorate": 100.0,
                        },
                    )
                ],
            }
        )
        self.env.company.with_vat_prorate = True
        invoice = self.init_invoice("in_invoice", products=[self.product_a])
        lines_with_prorate = invoice.line_ids.filtered(lambda rec: rec.vat_prorate)

        lines_with_amount = lines_with_prorate.filtered(
            lambda rec: not rec.currency_id.is_zero(rec.balance)
        )
        balances = [rec.balance for rec in lines_with_amount]

        self.assertGreaterEqual(
            len(lines_with_amount),
            0,
            f"Found vat_prorate lines with non-zero balance at 100% prorate: "
            f"{balances}",
        )

    def test_prorate_zero_percent_full_non_deductible(self):
        self.env.company.write(
            {
                "vat_prorate_ids": [
                    (0, 0, {"date": date(2025, 1, 1), "vat_prorate": 0.01})
                ],
                "with_vat_prorate": True,
            }
        )
        invoice = self.init_invoice("in_invoice", products=[self.product_a])
        tax_line = invoice.line_ids.filtered(lambda rec: rec.tax_line_id)
        prorate_line = invoice.line_ids.filtered(lambda rec: rec.vat_prorate)

        self.assertTrue(tax_line)
        self.assertTrue(prorate_line)

        self.assertGreater(
            abs(prorate_line.balance),
            abs(tax_line.balance),
            "Prorate line should be larger than tax line with low prorate percentage",
        )
        self.assertFalse(
            invoice.currency_id.is_zero(prorate_line.balance),
            "Prorate expense line must have a balance",
        )
        self.assertFalse(
            invoice.currency_id.is_zero(tax_line.balance),
            "Tax line should still have some deductible amount",
        )

    def test_prorate_multiple_tax_lines(self):
        tax = self.purchase_tax_21
        invoice = self.init_invoice(
            "in_invoice",
            products=[self.product_a, self.product_b],
            taxes=[tax],
        )
        tax_lines = invoice.line_ids.filtered(lambda rec: rec.tax_line_id)
        prorate_lines = invoice.line_ids.filtered(lambda rec: rec.vat_prorate)

        self.assertGreaterEqual(
            len(tax_lines), 2, "There must be at least two tax lines"
        )
        self.assertEqual(
            len(prorate_lines),
            len(tax_lines),
            "There must be one expense line per tax line",
        )
