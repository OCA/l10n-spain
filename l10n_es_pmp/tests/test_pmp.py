# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class TestPmp(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.company = cls.env.company
        cls.partner = cls.partner_a

        # We can use the accounts provided by AccountTestInvoicingCommon
        cls.expense_account = cls.company_data["default_account_expense"]

        # Invoice 1: Paid within 20 days (Amount 1000)
        cls.invoice1 = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": "2026-01-01",
                "date": "2026-01-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service 1",
                            "price_unit": 1000.0,
                            "account_id": cls.expense_account.id,
                        },
                    )
                ],
            }
        )
        cls.invoice1.action_post()

        # Pay Invoice 1 on 2026-01-21 (20 days later)
        payment_register = (
            cls.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=cls.invoice1.ids)
            .create(
                {
                    "payment_date": "2026-01-21",
                    "amount": 1000.0,
                }
            )
        )
        payment_register.action_create_payments()

        # Invoice 2: Unpaid (Pending). Date: 2026-11-01 (Amount 500)
        cls.invoice2 = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": "2026-11-01",
                "date": "2026-11-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service 2",
                            "price_unit": 500.0,
                            "account_id": cls.expense_account.id,
                        },
                    )
                ],
            }
        )
        cls.invoice2.action_post()

        # Invoice 3: Paid late (70 days).
        # Date: 2026-02-01. Paid on 2026-04-12 (Amount 200)
        cls.invoice3 = cls.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": cls.partner.id,
                "invoice_date": "2026-02-01",
                "date": "2026-02-01",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Service 3",
                            "price_unit": 200.0,
                            "account_id": cls.expense_account.id,
                        },
                    )
                ],
            }
        )
        cls.invoice3.action_post()

        payment_register3 = (
            cls.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=cls.invoice3.ids)
            .create(
                {
                    "payment_date": "2026-04-12",
                    "amount": 200.0,
                }
            )
        )
        payment_register3.action_create_payments()

    def test_01_pmp_calculation(self):
        # We calculate the PMP for the year 2026
        wizard = self.env["l10n.es.pmp.wizard"].create(
            {
                "company_id": self.company.id,
                "date_start": "2026-01-01",
                "date_end": "2026-12-31",
            }
        )

        wizard.action_calculate()

        self.assertEqual(wizard.state, "done")

        # Payments made: 1000 + 200 = 1200
        self.assertAlmostEqual(wizard.total_payments_made, 1200.0)

        # Pending payments: 500
        self.assertAlmostEqual(wizard.total_pending_payments, 500.0)

        # Ratio of paid operations:
        # Inv1: 1000 * 20 days = 20000
        # Inv3: 200 * 70 days = 14000
        # Total days * amount = 34000. Total amount = 1200.
        # Ratio = 34000 / 1200 = 28.3333333333
        self.assertAlmostEqual(wizard.ratio_paid_operations, 34000 / 1200, places=2)

        # Ratio of pending operations:
        # Inv2: Date 2026-11-01 to 2026-12-31 = 60 days
        # Ratio = 60 days
        self.assertAlmostEqual(wizard.ratio_pending_operations, 60.0)

        # Volume paid in legal term (<=60 days): Only Inv1 (1000)
        self.assertAlmostEqual(wizard.volume_paid_in_term, 1000.0)

        # % volume paid in term = 1000 / 1200 = 83.33%
        self.assertAlmostEqual(
            wizard.pct_volume_paid_in_term, (1000 / 1200) * 100, places=2
        )

        # Invoices paid in term = 1 (Inv1)
        self.assertEqual(wizard.invoices_paid_in_term, 1)

        # % invoices paid in term = 1 / 2 = 50%
        self.assertAlmostEqual(wizard.pct_invoices_paid_in_term, 50.0)

        # PMP = (ROP * TP + ROPP * TPP) / (TP + TPP)
        # PMP = ((28.333 * 1200) + (60 * 500)) / 1700
        # PMP = (34000 + 30000) / 1700 = 64000 / 1700 = 37.6470588235
        self.assertAlmostEqual(wizard.pmp, 64000 / 1700, places=2)
