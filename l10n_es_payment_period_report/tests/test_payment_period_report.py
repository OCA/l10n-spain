# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestPaymentPeriodReport(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.external_report_layout_id = cls.env.ref(
            "web.external_layout_standard"
        )

    def _create_supplier_invoice(self, invoice_date, amount, payment_term=None):
        return self._create_invoice_one_line(
            move_type="in_invoice",
            partner_id=self.partner_a,
            invoice_date=invoice_date,
            invoice_payment_term_id=payment_term,
            price_unit=amount,
            tax_ids=self.env["account.tax"],
            post=True,
        )

    def _pay_invoice(self, invoice, payment_date, amount=None):
        with Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids
            )
        ) as register_form:
            register_form.payment_date = payment_date
            if amount:
                register_form.amount = amount
        return register_form.record.action_create_payments()

    def _compute_report(self, year, **values):
        with Form(self.env["l10n.es.payment.period.report.wizard"]) as wizard_form:
            wizard_form.year = year
            for field_name, value in values.items():
                setattr(wizard_form, field_name, value)
        wizard = wizard_form.record
        wizard.action_compute()
        return wizard

    def test_report_summary(self):
        invoice_in_time = self._create_supplier_invoice("2024-01-01", 100)
        invoice_late = self._create_supplier_invoice("2024-01-01", 200)
        invoice_outside_period = self._create_supplier_invoice("2023-01-01", 300)
        invoice_not_paid = self._create_supplier_invoice("2024-01-01", 400)
        self._pay_invoice(invoice_in_time, "2024-02-15")
        self._pay_invoice(invoice_late, "2024-04-15")
        self._pay_invoice(invoice_outside_period, "2023-02-01")
        self._pay_invoice(invoice_not_paid, "2024-02-01", amount=150)
        self.assertEqual(invoice_in_time.payment_state, "paid")
        self.assertEqual(invoice_not_paid.payment_state, "partial")
        wizard = self._compute_report(2024)
        self.assertEqual(str(wizard.date_from), "2024-01-01")
        self.assertEqual(str(wizard.date_to), "2024-12-31")
        self.assertEqual(wizard.invoice_count, 2)
        self.assertEqual(wizard.invoice_count_within, 1)
        self.assertEqual(wizard.total_amount_paid, 300)
        self.assertEqual(wizard.total_amount_paid_within, 100)
        self.assertAlmostEqual(wizard.amount_within_percent, 100 / 300 * 100)
        self.assertAlmostEqual(wizard.invoice_within_percent, 50)
        self.assertAlmostEqual(
            wizard.average_payment_period, (100 * 45 + 200 * 105) / 300
        )
        self.assertEqual(wizard.line_ids.move_id, invoice_in_time + invoice_late)
        line_late = wizard.line_ids.filtered(lambda x: x.move_id == invoice_late)
        self.assertEqual(line_late.payment_days, 105)
        self.assertFalse(line_late.within_legal_period)
        self.assertEqual(
            line_late.display_name, f"{invoice_late.name} - {self.partner_a.name}"
        )
        self.assertEqual(wizard.get_report_file_name(), "payment_period_report_2024")
        action = wizard.action_view_lines()
        self.assertEqual(action["res_model"], wizard.line_ids._name)
        self.assertEqual(
            self.env[action["res_model"]].search(action["domain"]), wizard.line_ids
        )

    def test_report_partial_payments(self):
        """The payment date is the one of the payment that completes the invoice"""
        invoice = self._create_supplier_invoice("2024-01-01", 100)
        self._pay_invoice(invoice, "2024-01-20", amount=40)
        self._pay_invoice(invoice, "2024-03-31", amount=60)
        wizard = self._compute_report(2024)
        self.assertEqual(str(wizard.line_ids.payment_date), "2024-03-31")
        self.assertEqual(wizard.line_ids.payment_days, 90)
        self.assertFalse(wizard.line_ids.within_legal_period)
        wizard = self._compute_report(2024, legal_payment_days=90)
        self.assertTrue(wizard.line_ids.within_legal_period)

    def test_report_start_date_type(self):
        invoice = self._create_supplier_invoice(
            "2024-01-01",
            100,
            payment_term=self.env.ref("account.account_payment_term_30days"),
        )
        self.assertEqual(str(invoice.invoice_date_due), "2024-01-31")
        self._pay_invoice(invoice, "2024-03-15")
        wizard = self._compute_report(2024, date_start_type="invoice_date_due")
        self.assertEqual(str(wizard.line_ids.date_start), "2024-01-31")
        self.assertEqual(wizard.line_ids.payment_days, 44)
        self.assertTrue(wizard.line_ids.within_legal_period)

    def test_report_exports(self):
        invoice = self._create_supplier_invoice("2024-01-01", 100)
        self._pay_invoice(invoice, "2024-02-15")
        wizard = self._compute_report(2024)
        Report = self.env["ir.actions.report"]
        xlsx_action = wizard.action_export_xlsx()
        content, report_type = Report._render(xlsx_action["report_name"], wizard.ids)
        self.assertEqual(report_type, "xlsx")
        self.assertTrue(content)
        pdf_action = wizard.action_export_pdf()
        html = Report._render_qweb_html(pdf_action["report_name"], wizard.ids)[0]
        self.assertIn(invoice.name, html.decode())
