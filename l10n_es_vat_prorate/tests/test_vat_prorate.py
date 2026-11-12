# Copyright 2022 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date

from freezegun import freeze_time
from psycopg2 import IntegrityError, errors

from odoo import Command, exceptions
from odoo.modules.module import load_script
from odoo.tests import Form
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
        # Deal with analytics: the prorate line of the expense takes its analytic
        self.env.user.sudo().group_ids += self.env.ref(
            "analytic.group_analytic_accounting"
        )
        with (
            Form(invoice) as invoice_form,
            invoice_form.invoice_line_ids.edit(0) as line_form,
        ):
            line_form.analytic_distribution = {self.analytic_account.id: 100}
        self.assertEqual(6, len(invoice.line_ids))
        self.assertEqual(
            1,
            len(
                invoice.line_ids.filtered(
                    lambda r: r.tax_line_id and r.analytic_distribution
                )
            ),
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
        # IGIC is not VAT
        for name in ("igic_sop_7", "igic_ISP7"):
            self.assertEqual(tax(name).l10n_es_applicability, "03", name)
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

    def _tax_lines(self, move):
        return move.line_ids.filtered("tax_line_id").sorted(
            lambda line: (line.vat_prorate, line.account_id.code, line.balance)
        )

    def test_prorate_default_date(self):
        with freeze_time("2030-02-03"):
            prorate_form = Form(self.env["res.company.vat.prorate"])
            self.assertEqual(prorate_form.date, date(2030, 2, 3))

    def test_prorate_company_deletion(self):
        company = self.env["res.company"].sudo().create({"name": "Prorate company"})
        prorate = self.env["res.company.vat.prorate"].create(
            {"company_id": company.id, "date": date(2020, 1, 1), "vat_prorate": 50}
        )
        company.unlink()
        self.assertFalse(prorate.exists())

    def test_prorate_amounts(self):
        """Prorate of 20 %: the tax account keeps the deductible 20 % and the rest
        goes to the account of each expense line."""
        expense = self.company_data["default_account_expense"]
        other_expense = self.copy_account(expense)
        tax = self._tax("p_iva21_bc")
        account_472 = tax.invoice_repartition_line_ids.account_id
        invoice = self._create_bill(
            [(100, tax, expense), (200, tax, other_expense), (300, tax, expense)]
        )
        self.assertRecordValues(
            self._tax_lines(invoice),
            [
                # 21 % of 600 = 126, 20 % deductible
                {"account_id": account_472.id, "balance": 25.2, "vat_prorate": False},
                {"account_id": expense.id, "balance": 67.2, "vat_prorate": True},
                {"account_id": other_expense.id, "balance": 33.6, "vat_prorate": True},
            ],
        )
        self.assertAlmostEqual(invoice.amount_total, 726)
        # Refund: same split with the opposite sign
        refund = self._create_bill([(100, tax, expense)], move_type="in_refund")
        self.assertRecordValues(
            self._tax_lines(refund),
            [
                {"account_id": account_472.id, "balance": -4.2, "vat_prorate": False},
                {"account_id": expense.id, "balance": -16.8, "vat_prorate": True},
            ],
        )

    def test_prorate_self_assessed_tax_amounts(self):
        """Intra-community acquisition: only the deductible side is prorated, the
        output VAT is kept whole."""
        tax = self._tax("p_iva21_ic_bc")
        expense = self.company_data["default_account_expense"]
        invoice = self._create_bill([(100, tax, expense)])
        account_472, account_477 = (
            tax.invoice_repartition_line_ids.filtered(
                lambda line: line.factor_percent > 0 and line.account_id
            ).account_id,
            tax.invoice_repartition_line_ids.filtered(
                lambda line: line.factor_percent < 0
            ).account_id,
        )
        self.assertRecordValues(
            invoice.line_ids.filtered("tax_line_id").sorted("balance"),
            [
                {"account_id": account_477.id, "balance": -21, "vat_prorate": False},
                {"account_id": account_472.id, "balance": 4.2, "vat_prorate": False},
                {"account_id": expense.id, "balance": 16.8, "vat_prorate": True},
            ],
        )

    def test_prorate_aeat_tax_info(self):
        """The deductible quota declared to the AEAT (SII, VAT book) is the
        prorated one, while the quota is the whole one."""
        tax = self._tax("p_iva21_bc")
        tax_ic = self._tax("p_iva21_ic_bc")
        invoice = self._create_bill([(100, tax, None), (200, tax_ic, None)])
        invoice.action_post()
        tax_info = invoice._get_aeat_tax_info()
        self.assertAlmostEqual(tax_info[tax]["base"], 100)
        self.assertAlmostEqual(tax_info[tax]["amount"], 21)
        self.assertAlmostEqual(tax_info[tax]["deductible_amount"], 4.2)
        self.assertAlmostEqual(tax_info[tax_ic]["base"], 200)
        self.assertAlmostEqual(tax_info[tax_ic]["amount"], 42)
        self.assertAlmostEqual(tax_info[tax_ic]["deductible_amount"], 8.4)

    def test_prorate_tax_type_rule_taxes(self):
        """Taxes selected by their type (7.5 %, 5 % investment goods, imports) are
        prorated in the invoices."""
        expense = self.company_data["default_account_expense"]
        for name, amount in (
            ("p_iva7-5_bc", 7.5),
            ("p_iva5_bi", 5),
            ("p_iva21_ibc", 21),
        ):
            tax = self._tax(name)
            tax.active = True
            invoice = self._create_bill([(1000, tax, expense)])
            account_472 = tax.invoice_repartition_line_ids.account_id
            self.assertRecordValues(
                self._tax_lines(invoice),
                [
                    {"account_id": account_472.id, "balance": 2 * amount},
                    {"account_id": expense.id, "balance": 8 * amount},
                ],
            )

    def test_prorate_refund_previous_year(self):
        """A refund dated in a later year takes the prorate of its invoice."""
        tax = self._tax("p_iva21_bc")
        expense = self.company_data["default_account_expense"]
        # Prorate of 2000: 10 %
        invoice = self._create_bill([(100, tax, expense)], invoice_date="2000-06-01")
        invoice.action_post()
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=invoice.ids, active_model="account.move")
            .create({"journal_id": invoice.journal_id.id, "date": date(2001, 2, 1)})
        )
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        self.assertEqual(refund.date, date(2001, 2, 1))
        self.assertEqual(refund.prorate_id.vat_prorate, 10)
        self.assertRecordValues(
            self._tax_lines(refund),
            [
                {"balance": -2.1, "vat_prorate": False},
                {"balance": -18.9, "vat_prorate": True},
            ],
        )

    def test_prorate_reset_to_draft(self):
        tax = self._tax("p_iva21_bc")
        invoice = self._create_bill([(100, tax, None)])
        invoice.action_post()
        invoice.button_draft()
        invoice.action_post()
        self.assertRecordValues(
            self._tax_lines(invoice),
            [
                {"balance": 4.2, "vat_prorate": False},
                {"balance": 16.8, "vat_prorate": True},
            ],
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

    def _create_deductible_bill(self, lines, prorate_type="general"):
        """Vendor bill of 2020 (prorate of 80 %) entered through the form, with one
        line per (price, deductible percentage, prorated) given, all with 21 % VAT.
        """
        self.env.company.vat_prorate_ids = [
            Command.create(
                {
                    "date": date(2020, 1, 1),
                    "vat_prorate": 80,
                    "type": prorate_type,
                    "special_vat_prorate_default": True,
                }
            )
        ]
        bill_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = self.partner_a
        bill_form.invoice_date = date(2020, 3, 1)
        for price, deductible_percentage, with_vat_prorate in lines:
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.name = "Fuel"
                line_form.price_unit = price
                line_form.tax_ids.clear()
                line_form.tax_ids.add(self._tax("p_iva21_bc"))
                line_form.deductible_percentage = deductible_percentage
                if prorate_type == "special":
                    line_form.with_vat_prorate = with_vat_prorate
        return bill_form.save()

    def _assert_deductible_lines(self, move, expected):
        """Check the journal items of the move by kind, and that it is balanced."""
        expense = self.company_data["default_account_expense"]
        account_472 = self._tax("p_iva21_bc").invoice_repartition_line_ids.account_id
        payable = self.company_data["default_account_payable"]
        # Private part: account for non deductible amounts of the journal
        private = move.journal_id.non_deductible_account_id
        accounts = {
            "expense": expense,
            "472": account_472,
            "payable": payable,
            "private": private,
        }
        self.assertRecordValues(
            move.line_ids.sorted(
                lambda line: (line.display_type, line.vat_prorate, line.balance)
            ),
            [
                {
                    "display_type": display_type,
                    "account_id": accounts[account].id,
                    "balance": balance,
                    "vat_prorate": vat_prorate,
                }
                for display_type, account, balance, vat_prorate in expected
            ],
        )
        self.assertAlmostEqual(sum(move.line_ids.mapped("balance")), 0)

    def test_prorate_on_deductible_part(self):
        """Car fuel used 50 % in the activity (art. 95 LIVA) with a general prorate of
        80 %: the prorate applies on the quota left deductible by the non deductible
        percentage (art. 104.Uno LIVA). 21 x 0.5 x 0.8 = 8.40 deductible; 10.50 of
        private part (Odoo core) and 2.10 of prorate not deductible."""
        bill = self._create_deductible_bill([(100, 0.5, True)])
        bill.action_post()
        self._assert_deductible_lines(
            bill,
            [
                ("non_deductible_product", "expense", -50, False),
                ("non_deductible_product_total", "private", 50, False),
                ("non_deductible_tax", "private", 10.5, False),
                ("payment_term", "payable", -121, False),
                ("product", "expense", 100, False),
                ("tax", "472", 8.4, False),
                ("tax", "expense", 2.1, True),
            ],
        )
        tax_info = bill._get_aeat_tax_info()[self._tax("p_iva21_bc")]
        self.assertAlmostEqual(tax_info["amount"], 10.5)
        self.assertAlmostEqual(tax_info["deductible_amount"], 8.4)

    def test_prorate_on_deductible_part_refund(self):
        """The refund of the bill reverses the same split."""
        bill = self._create_deductible_bill([(100, 0.5, True)])
        bill.action_post()
        wizard = (
            self.env["account.move.reversal"]
            .with_context(active_ids=bill.ids, active_model="account.move")
            .create({"journal_id": bill.journal_id.id, "date": date(2020, 4, 1)})
        )
        wizard.reverse_moves()
        refund = wizard.new_move_ids
        self.assertEqual(refund.move_type, "in_refund")
        self._assert_deductible_lines(
            refund,
            [
                ("non_deductible_product", "expense", 50, False),
                ("non_deductible_product_total", "private", -50, False),
                ("non_deductible_tax", "private", -10.5, False),
                ("payment_term", "payable", 121, False),
                ("product", "expense", -100, False),
                ("tax", "472", -8.4, False),
                ("tax", "expense", -2.1, True),
            ],
        )

    def test_special_prorate_on_deductible_part(self):
        """Special prorate: the prorated line and the one fully deductible both
        start from their deductible quota."""
        bill = self._create_deductible_bill(
            [(100, 0.5, True), (200, 0.5, False)], prorate_type="special"
        )
        bill.action_post()
        # Prorated line: 10.50 x 0.8 = 8.40; other line: 21 deductible
        self._assert_deductible_lines(
            bill,
            [
                ("non_deductible_product", "expense", -100, False),
                ("non_deductible_product", "expense", -50, False),
                ("non_deductible_product_total", "private", 150, False),
                ("non_deductible_tax", "private", 31.5, False),
                ("payment_term", "payable", -363, False),
                ("product", "expense", 100, False),
                ("product", "expense", 200, False),
                ("tax", "472", 29.4, False),
                ("tax", "expense", 2.1, True),
            ],
        )
        # Without prorated lines the tax line keeps the whole deductible quota
        bill.button_draft()
        with Form(bill) as bill_form, bill_form.invoice_line_ids.edit(0) as line_form:
            line_form.with_vat_prorate = False
        bill.action_post()
        self._assert_deductible_lines(
            bill,
            [
                ("non_deductible_product", "expense", -100, False),
                ("non_deductible_product", "expense", -50, False),
                ("non_deductible_product_total", "private", 150, False),
                ("non_deductible_tax", "private", 31.5, False),
                ("payment_term", "payable", -363, False),
                ("product", "expense", 100, False),
                ("product", "expense", 200, False),
                ("tax", "472", 31.5, False),
            ],
        )

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
