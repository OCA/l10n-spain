# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from psycopg2 import IntegrityError

from odoo import exceptions
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVatProrate(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass(chart_template_ref="l10n_es.account_chart_template_pymes")
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

    # Put `zzz` for making sure that the test is executed in last place, as the cursor
    # gets incoherent after returning from the SQL constraint violation
    @mute_logger("odoo.sql_db")
    def test_zzz_company_vat_prorate_out_of_range(self):
        with self.assertRaises(IntegrityError):
            self.env.company.vat_prorate_ids[0].vat_prorate = 200

    def test_no_company_vat_prorate_information(self):
        with self.assertRaises(exceptions.ValidationError):
            self.env.company.write({"vat_prorate_ids": False})

    def test_company_configuration(self):
        self.assertTrue(self.env.company.with_vat_prorate)
        self.assertTrue(self.env.company.prorrate_asset_account_id)
        self.assertTrue(self.env.company.prorrate_investment_account_id)
        self.env.company.write({"with_vat_prorate": False})
        self.assertFalse(self.env.company.prorrate_asset_account_id)
        self.assertFalse(self.env.company.prorrate_investment_account_id)

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
        self.assertTrue(
            invoice.line_ids.filtered(
                lambda r: r.tax_line_id
                and r.account_id == self.product_a.property_account_expense_id
            )
        )
        self.assertTrue(
            invoice.line_ids.filtered(
                lambda r: r.tax_line_id
                and r.account_id == self.product_b.property_account_expense_id
            )
        )
        # Deal with analytics
        invoice.line_ids[0].analytic_distribution = {self.analytic_account.id: 100}
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(
            1,
            len(
                invoice.line_ids.filtered(
                    lambda r: r.tax_line_id and r.analytic_distribution
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
        tax_lines = invoice.line_ids.filtered(lambda r: r.tax_line_id)
        self.assertEqual(2, len(tax_lines))
        self.assertEqual(1, len(tax_lines.filtered("vat_prorate")))
        # One of the tax lines should have expense account and the other the tax account
        self.assertNotEqual(tax_lines[0].account_id, tax_lines[1].account_id)

    def test_prorate_asset_in_invoice(self):
        self.product_b.property_account_expense_id = self.company_data[
            "default_account_assets"
        ]
        invoice = self.init_invoice("in_invoice", products=[self.product_b])
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))
        self.assertFalse(
            invoice.line_ids.filtered(
                lambda r: r.tax_line_id
                and r.account_id == self.product_b.property_account_expense_id
            )
        )

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
        self.assertEqual(len(tax_lines), 2)
        # One of the tax lines should have expense account and the other the tax account
        self.assertNotEqual(tax_lines[0].account_id, tax_lines[1].account_id)
