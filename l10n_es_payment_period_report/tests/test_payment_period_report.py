# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import xlrd

from odoo import Command
from odoo.tests import Form
from odoo.tests.common import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentPeriodReport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.bank_journal = cls.company_data["default_journal_bank"]
        cls.expense_account = cls.company_data["default_account_expense"]
        # A company without document layout gets the layout configurator first
        cls.company.external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )
        # Spanish chart of accounts codes in the scope of the report
        cls.payable_account = cls.env["account.account"].create(
            {
                "code": "400099",
                "name": "Suppliers",
                "user_type_id": cls.env.ref("account.data_account_type_payable").id,
                "reconcile": True,
                "company_id": cls.company.id,
            }
        )
        cls.partner_a.with_company(
            cls.company
        ).property_account_payable_id = cls.payable_account

    def _create_supplier_invoice(
        self,
        invoice_date,
        amount,
        move_type="in_invoice",
        account=None,
        date=None,
    ):
        invoice = self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "date": date or invoice_date,
                "company_id": self.company.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Test line",
                            "quantity": 1,
                            "price_unit": amount,
                            "account_id": (account or self.expense_account).id,
                            "tax_ids": [Command.clear()],
                        }
                    )
                ],
            }
        )
        invoice.action_post()
        return invoice

    def _register_payment(self, invoice, payment_date, amount=None):
        wizard = (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoice.ids)
            .create(
                {
                    "payment_date": payment_date,
                    "journal_id": self.bank_journal.id,
                    "amount": amount or invoice.amount_residual,
                    "payment_difference_handling": "open",
                }
            )
        )
        return wizard._create_payments()

    def _assign_credit_note(self, invoice, refund):
        refund_line = refund.line_ids.filtered(
            lambda line: line.account_id.internal_type == "payable"
        )
        invoice.js_assign_outstanding_line(refund_line.id)

    def _export_xlsx_rows(self, wizard):
        action = wizard.action_export_xlsx()
        report = self.env["ir.actions.report"]._get_report_from_name(
            action["report_name"]
        )
        content, report_type = report._render(wizard.ids)
        self.assertEqual(report_type, "xlsx")
        sheet = xlrd.open_workbook(file_contents=content).sheet_by_index(0)
        return [sheet.row_values(row) for row in range(sheet.nrows)]

    def _get_row(self, rows, label):
        return next(row for row in rows if row[0] == label)

    def _open_wizard(self, method, year=2024):
        with Form(self.env["l10n.es.payment.period.report.wizard"]) as wizard_form:
            wizard_form.year = year
            wizard_form.method = method
        wizard = wizard_form.save()
        wizard.action_compute()
        return wizard

    def test_normal_method(self):
        invoice_in_time = self._create_supplier_invoice("2024-01-01", 100)
        self._register_payment(invoice_in_time, "2024-02-15")
        invoice_late = self._create_supplier_invoice("2024-01-01", 200)
        self._register_payment(invoice_late, "2024-04-15")
        invoice_previous_year = self._create_supplier_invoice("2023-01-01", 300)
        self._register_payment(invoice_previous_year, "2023-02-01")
        # Instalments are weighted with their own days
        invoice_instalments = self._create_supplier_invoice("2024-01-01", 1000)
        self._register_payment(invoice_instalments, "2024-01-11", 500)
        self._register_payment(invoice_instalments, "2024-03-31", 500)
        # A credit note settles part of the invoice without being a payment
        invoice_refunded = self._create_supplier_invoice("2024-06-01", 300)
        refund = self._create_supplier_invoice("2024-06-10", 100, "in_refund")
        self._assign_credit_note(invoice_refunded, refund)
        self._register_payment(invoice_refunded, "2024-07-01")
        # Pending at the end of the period although it is paid afterwards
        invoice_pending = self._create_supplier_invoice("2024-11-30", 400)
        self._register_payment(invoice_pending, "2025-01-10")

        wizard = self._open_wizard("normal")

        paid = wizard.line_ids.filtered(lambda line: line.line_type == "paid")
        pending = wizard.line_ids - paid
        self.assertEqual(
            sorted(paid.mapped(lambda line: (line.move_id.id, line.amount, line.days))),
            sorted(
                [
                    (invoice_in_time.id, 100, 45),
                    (invoice_late.id, 200, 105),
                    (invoice_instalments.id, 500, 10),
                    (invoice_instalments.id, 500, 90),
                    (invoice_refunded.id, 200, 30),
                ]
            ),
        )
        self.assertEqual(pending.move_id, invoice_pending)
        self.assertEqual(pending.amount, 400)
        self.assertEqual(pending.days, 31)
        self.assertFalse(pending.payment_date)
        self.assertEqual(wizard.total_amount_paid, 1500)
        self.assertEqual(wizard.total_amount_pending, 400)
        paid_weighted = 100 * 45 + 200 * 105 + 500 * 10 + 500 * 90 + 200 * 30
        self.assertAlmostEqual(wizard.paid_operations_ratio, paid_weighted / 1500)
        self.assertAlmostEqual(wizard.pending_operations_ratio, 31)
        self.assertAlmostEqual(
            wizard.average_payment_period, (paid_weighted + 400 * 31) / 1900
        )
        self.assertEqual(wizard.total_amount_paid_within, 800)
        self.assertAlmostEqual(wizard.amount_within_percent, 800 / 1500 * 100)
        # The invoice paid in instalments has one payment out of the legal period
        self.assertEqual(wizard.invoice_count, 4)
        self.assertEqual(wizard.invoice_count_within, 2)
        self.assertAlmostEqual(wizard.invoice_within_percent, 50)
        self.assertEqual(wizard.get_report_file_name(), "payment_period_report_2024")
        self.assertEqual(wizard.action_view_lines()["res_model"], wizard.line_ids._name)
        rows = self._export_xlsx_rows(wizard)
        pmp_row = self._get_row(rows, "Average payment period to suppliers (days)")
        self.assertAlmostEqual(pmp_row[6], wizard.average_payment_period)
        self.assertEqual(self._get_row(rows, "Total payments pending")[6], 400)
        detail = [row for row in rows if row[8] in ("Yes", "No")]
        self.assertEqual(len(detail), 6)
        self.assertIn(
            ["Pending payment", invoice_pending.name, ""], [row[:3] for row in detail]
        )

    def test_pending_invoice_posted_after_period(self):
        invoice = self._create_supplier_invoice("2024-12-20", 100, date="2025-01-05")
        self.assertEqual(invoice.date.isoformat(), "2025-01-05")
        wizard = self._open_wizard("normal")
        self.assertEqual(wizard.line_ids.move_id, invoice)
        self.assertEqual(wizard.line_ids.line_type, "pending")
        self.assertEqual(wizard.line_ids.days, 11)
        wizard.date_start_type = "date"
        wizard.action_compute()
        self.assertFalse(wizard.line_ids)

    def test_abbreviated_method(self):
        account_model = self.env["account.account"]
        expense_type = self.env.ref("account.data_account_type_expenses")
        purchase = account_model.create(
            {
                "code": "600099",
                "name": "Purchases",
                "user_type_id": expense_type.id,
                "company_id": self.company.id,
            }
        )
        service = account_model.create(
            {
                "code": "621099",
                "name": "Leases",
                "user_type_id": expense_type.id,
                "company_id": self.company.id,
            }
        )
        invoice_previous_year = self._create_supplier_invoice(
            "2023-12-01", 1000, account=purchase
        )
        self._register_payment(invoice_previous_year, "2024-01-20")
        invoice_purchase = self._create_supplier_invoice(
            "2024-03-01", 2000, account=purchase
        )
        self._register_payment(invoice_purchase, "2024-04-01")
        self._create_supplier_invoice("2024-05-01", 1000, account=service)

        wizard = self._open_wizard("abbreviated")

        self.assertEqual(wizard.computed_method, "abbreviated")
        self.assertFalse(wizard.line_ids)
        self.assertEqual(wizard.creditor_opening_balance, 1000)
        self.assertEqual(wizard.creditor_closing_balance, 1000)
        self.assertEqual(wizard.creditor_average_balance, 1000)
        self.assertEqual(wizard.net_purchases, 2000)
        self.assertEqual(wizard.external_services, 1000)
        self.assertAlmostEqual(wizard.average_payment_period, 1000 / 3000 * 365)
        rows = self._export_xlsx_rows(wizard)
        pmp_row = self._get_row(rows, "Average payment period to suppliers (days)")
        self.assertAlmostEqual(pmp_row[1], 1000 / 3000 * 365)
        self.assertEqual(self._get_row(rows, "Net purchases")[1], 2000)
        # Switching the method clears the figures of the other one
        wizard.method = "normal"
        wizard.action_compute()
        self.assertEqual(wizard.computed_method, "normal")
        self.assertFalse(wizard.creditor_average_balance)
        self.assertEqual(wizard.total_amount_paid, 3000)
