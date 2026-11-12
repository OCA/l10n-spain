# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from psycopg2 import IntegrityError, errors

from odoo import Command, exceptions
from odoo.modules.module import load_script
from odoo.tests.common import tagged
from odoo.tools import mute_logger

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVatProrate(AccountTestInvoicingCommon):
    # Because we are using the AccountTestInvoicingCommon the final user is
    # 'Because I am accountman!' so we need to add the account_aeat
    # group to create account.update.vat_prorate records
    @classmethod
    def get_default_groups(cls):
        groups = super().get_default_groups()
        group_account_aeat = cls.env.ref(
            "l10n_es_aeat.group_account_aeat", raise_if_not_found=True
        )
        if group_account_aeat:
            return groups | group_account_aeat
        return groups

    @classmethod
    @AccountTestInvoicingCommon.setup_chart_template("es_pymes")
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
        vat_prorate_line = self.env.company.vat_prorate_ids[0]
        with self.assertRaises(IntegrityError):
            vat_prorate_line.vat_prorate = 200

    @mute_logger("odoo.sql_db")
    def test_company_special_vat_prorate_out_of_range(self):
        # A error should be displayed if special prorates are 100%
        prorate_id = self.env.company.vat_prorate_ids[0]
        with self.assertRaises(errors.CheckViolation):
            prorate_id.write({"type": "special", "vat_prorate": 100})

    def test_no_company_vat_prorate_information(self):
        self.assertTrue(self.env.company.vat_prorate_ids)
        with self.assertRaises(exceptions.ValidationError):
            self.env.company.write({"vat_prorate_ids": False})

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
        invoice.line_ids[0].analytic_distribution = {self.analytic_account.id: 100}
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(
            1,
            len(invoice.line_ids.filtered(lambda r: r.analytic_distribution)),
        )

    def test_prorate_tax_with_prorate_account(self):
        # 21% EU S (Services) tax
        tax = self.env.ref(
            f"account.{self.env.company.id}_account_tax_template_p_iva21_sp_in"
        )
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b], taxes=[tax]
        )
        self.assertEqual(7, len(invoice.line_ids))
        self.assertEqual(4, len(invoice.line_ids.filtered(lambda r: r.tax_line_id)))

    def test_prorate_taxes_from_tax_type(self):
        """The taxes to prorate come from the Odoo core tax type of each tax, so the
        7.5 % or 5 % investment goods taxes are prorated as the 21 % ones."""

        def tax(name):
            return self.env.ref(
                f"account.{self.env.company.id}_account_tax_template_{name}"
            )

        for name in ("p_iva21_bc", "p_iva7-5_bc", "p_iva5_bi", "p_iva21_ibc"):
            self.assertTrue(tax(name).with_vat_prorate, name)
            self.assertFalse(tax(name).prorate_account_ids, name)
        for name in ("p_iva10_nd", "p_irpf19", "s_iva21b", "p_iva0_bc"):
            self.assertFalse(tax(name).with_vat_prorate, name)
        # Self-assessed taxes: only the deductible account is prorated
        for name in ("p_iva7-5_ic_bc", "p_iva21_sp_in", "p_iva21_isp"):
            self.assertTrue(tax(name).with_vat_prorate, name)
            self.assertEqual(
                tax(name).prorate_account_ids.mapped("code"), ["472000"], name
            )
        # A tax created by the user follows the same rule
        new_tax = tax("p_iva21_bc").copy({"name": "IVA 21% propio"})
        self.assertTrue(new_tax.with_vat_prorate)
        new_tax.l10n_es_type = "no_deducible"
        self.assertFalse(new_tax.with_vat_prorate)

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
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(2, len(invoice.line_ids.filtered("vat_prorate")))

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
        self.assertEqual(4, len(invoice.line_ids))
        self.assertEqual(0, len(invoice.line_ids.filtered("vat_prorate")))

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
        invoice.write(
            {
                "invoice_line_ids": [
                    (1, line.id, {"with_vat_prorate": False})
                    for line in invoice.invoice_line_ids.filtered(
                        lambda r: r.product_id == self.product_a
                    )
                ]
            }
        )
        self.assertEqual(5, len(invoice.line_ids))
        self.assertEqual(1, len(invoice.line_ids.filtered("vat_prorate")))
        inv_line_b = invoice.line_ids.filtered(lambda r: r.product_id == self.product_b)
        prorate_id = self.env.company.vat_prorate_ids[0]
        self.assertAlmostEqual(
            invoice.line_ids.filtered("vat_prorate").debit,
            inv_line_b.price_subtotal
            * inv_line_b.tax_ids[:1].amount
            * (100 - prorate_id.vat_prorate)
            / 10000,
        )

    def test_prorate_update_with_wizard(self):
        wizard = (
            self.env["account.update.vat_prorate"]
            .with_company(self.env.company)
            .create({})
        )
        self.assertEqual(wizard.company_id.id, self.env.company.id)
        self.assertTrue(wizard.with_vat_prorate)
        self.assertEqual(len(wizard.vat_prorate_ids), 2)
        # Update company data through the wizard
        wizard.with_vat_prorate = False
        wizard.vat_prorate_ids = wizard.vat_prorate_ids[1:]
        wizard.execute()
        self.assertFalse(self.env.company.with_vat_prorate)
        self.assertEqual(len(self.env.company.vat_prorate_ids), 1)

    def test_prorate_with_account(self):
        test_account = self.env["account.account"].create(
            {
                "code": "9999999",
                "name": "Test Account",
                "account_type": "asset_current",
                "company_ids": [Command.link(self.env.company.id)],
            }
        )
        self.env.company.vat_prorate_ids[0].write({"account_id": test_account.id})
        invoice = self.init_invoice(
            "in_invoice", products=[self.product_a, self.product_b]
        )
        self.assertEqual(
            set(invoice.line_ids.filtered("vat_prorate").mapped("account_id").ids),
            {test_account.id},
        )

    def _tax(self, name):
        return self.env.ref(
            f"account.{self.env.company.id}_account_tax_template_{name}"
        )

    def _create_bill(self, lines, move_type="in_invoice", invoice_date="2019-01-01"):
        """Vendor bill with one line per (price, tax, account) given."""
        return self.env["account.move"].create(
            {
                "move_type": move_type,
                "partner_id": self.partner_a.id,
                "invoice_date": invoice_date,
                "date": invoice_date,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": f"Line {price}",
                            "price_unit": price,
                            "tax_ids": [Command.set(tax.ids)],
                            "account_id": (
                                account or self.company_data["default_account_expense"]
                            ).id,
                        }
                    )
                    for price, tax, account in lines
                ],
            }
        )

    def test_no_prorate_in_journal_entry(self):
        """Writing a journal entry with a purchase tax doesn't add prorate lines."""
        tax = self._tax("p_iva21_bc")
        expense = self.company_data["default_account_expense"]
        entry = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": "2019-01-01",
                "line_ids": [
                    Command.create(
                        {
                            "name": "Expense",
                            "account_id": expense.id,
                            "balance": 100,
                            "tax_ids": [Command.set(tax.ids)],
                        }
                    ),
                    Command.create(
                        {
                            "name": "Counterpart",
                            "account_id": self.company_data[
                                "default_account_payable"
                            ].id,
                            "balance": -121,
                        }
                    ),
                ],
            }
        )
        lines = entry.line_ids
        self.assertEqual(len(lines.filtered("tax_line_id")), 1)
        entry.date = "2019-01-02"
        self.assertEqual(entry.line_ids, lines)
        self.assertFalse(entry.line_ids.filtered("vat_prorate"))

    def test_prorate_mark_kept_on_tax_edition(self):
        """The mark set by the user in a tax survives the edition of its accounts."""
        tax = self._tax("p_iva21_bc")
        self.assertTrue(tax.with_vat_prorate)
        tax.with_vat_prorate = False
        tax_line = tax.invoice_repartition_line_ids.filtered(
            lambda line: line.repartition_type == "tax"
        )
        tax_line.account_id = self.copy_account(tax_line.account_id)
        self.assertFalse(tax.with_vat_prorate)

    def test_prorate_with_non_deductible_percentage(self):
        tax = self._tax("p_iva21_bc")
        invoice = self._create_bill([(100, tax, None)])
        with self.assertRaises(exceptions.ValidationError):
            invoice.invoice_line_ids.deductible_percentage = 0.5

    def test_migration_marks_new_taxes_only(self):
        """The 20.0 migration marks the taxes that the tax type adds, not the ones of
        the 19.0 list that the user unmarked."""
        try:
            import openupgradelib  # noqa: F401
        except ImportError:
            self.skipTest("openupgradelib is not installed")
        unmarked_by_user = self._tax("p_iva21_bc")
        new_tax = self._tax("p_iva7-5_bc")
        (unmarked_by_user | new_tax).with_vat_prorate = False
        script = load_script(
            "l10n_es_vat_prorate/migrations/20.0.1.0.0/post-migration.py",
            "l10n_es_vat_prorate_post_migration",
        )
        script.migrate.__wrapped__(self.env, "19.0.1.0.0")
        self.assertFalse(unmarked_by_user.with_vat_prorate)
        self.assertTrue(new_tax.with_vat_prorate)
