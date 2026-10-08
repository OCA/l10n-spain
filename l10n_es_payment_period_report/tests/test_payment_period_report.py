# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentPeriodReport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.payable_account = cls.company_data["default_account_payable"]
        cls.expense_account = cls.company_data["default_account_expense"]

    def _create_supplier_invoice(self, invoice_date, amount):
        invoice = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "date": invoice_date,
                "company_id": self.company.id,
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Test line",
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": self.expense_account.id,
                            "tax_ids": [(6, 0, [])],
                        },
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _pay_invoice(self, invoice, payment_date, amount=False):
        amount = amount or invoice.amount_total
        payment_move = self.env["account.move"].create(
            {
                "date": payment_date,
                "journal_id": self.bank_journal.id,
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Supplier payment",
                            "partner_id": invoice.partner_id.id,
                            "account_id": self.payable_account.id,
                            "debit": amount,
                            "credit": 0.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Supplier payment",
                            "account_id": self.bank_journal.default_account_id.id,
                            "debit": 0.0,
                            "credit": amount,
                        },
                    ),
                ],
            }
        )
        payment_move.action_post()
        lines = (invoice.line_ids + payment_move.line_ids).filtered(
            lambda line: line.account_id.internal_type == "payable"
            and not line.reconciled
        )
        lines.reconcile()
        return payment_move

    def test_report_summary(self):
        invoice_in_time = self._create_supplier_invoice("2024-01-01", 100)
        invoice_late = self._create_supplier_invoice("2024-01-01", 200)
        invoice_outside_period = self._create_supplier_invoice("2023-01-01", 300)
        self._pay_invoice(invoice_in_time, "2024-02-15")
        self._pay_invoice(invoice_late, "2024-04-15")
        self._pay_invoice(invoice_outside_period, "2023-02-01")
        self.assertTrue(
            invoice_in_time.line_ids.filtered(
                lambda line: line.account_id.internal_type == "payable"
            ).full_reconcile_id
        )

        wizard = self.env["l10n.es.payment.period.report.wizard"].create(
            {
                "company_id": self.company.id,
                "year": 2024,
                "date_from": "2024-01-01",
                "date_to": "2024-12-31",
                "legal_payment_days": 60,
            }
        )
        wizard.action_compute()

        self.assertEqual(wizard.invoice_count, 2)
        self.assertEqual(wizard.invoice_count_within, 1)
        self.assertEqual(wizard.total_amount_paid, 300)
        self.assertEqual(wizard.total_amount_paid_within, 100)
        self.assertAlmostEqual(wizard.amount_within_percent, 100 / 300 * 100)
        self.assertAlmostEqual(wizard.invoice_within_percent, 50)
        self.assertEqual(len(wizard.line_ids), 2)
        self.assertEqual(wizard.get_report_file_name(), "payment_period_report_2024")
        self.assertEqual(wizard.action_view_lines()["res_model"], wizard.line_ids._name)
        self.assertTrue(wizard.action_export_pdf())
        self.assertTrue(wizard.action_export_xlsx())
