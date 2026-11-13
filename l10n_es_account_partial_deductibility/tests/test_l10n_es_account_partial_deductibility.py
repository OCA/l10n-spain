# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict

from odoo.tests import Form, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestL10nEsAccountPartialDeductibility(AccountTestInvoicingCommon):
    """The private part of a partially deductible vendor bill line (art. 95
    LIVA) stays on the account of the line with its non deductible VAT (PGC,
    norma 12ª), whatever the Private Share Account of the purchase journal."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("es")
    def setUpClass(cls):
        super().setUpClass()
        cls.tax = cls.company_data["default_tax_purchase"]
        cls.journal = cls.company_data["default_journal_purchase"]
        cls.usd = cls.setup_other_currency("USD")

    def _account(self, code, company):
        return self.env["account.account"].search(
            [("company_ids", "=", company.id), ("code", "=", code)]
        )

    def _create_bill(self, lines, journal=None, partner=None, currency=None):
        bill_form = Form(
            self.env["account.move"].with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = partner or self.partner_a
        bill_form.invoice_date = "2026-01-15"
        bill_form.journal_id = journal or self.journal
        if currency:
            bill_form.currency_id = currency
        for account_code, price_unit, deductible_percentage in lines:
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.name = "Mixed use purchase"
                line_form.account_id = self._account(
                    account_code, bill_form.journal_id.company_id
                )
                line_form.price_unit = price_unit
                if not bill_form.fiscal_position_id:
                    line_form.tax_ids.clear()
                    line_form.tax_ids.add(
                        bill_form.journal_id.company_id.account_purchase_tax_id
                    )
                line_form.deductible_percentage = deductible_percentage
        return bill_form.save()

    def _assert_balances(self, move, expected):
        balances = defaultdict(float)
        for line in move.line_ids:
            code = line.account_id.code
            balances["payable" if line.display_type == "payment_term" else code] += (
                line.balance
            )
        self.assertEqual(
            {code: round(balance, 2) for code, balance in balances.items()}, expected
        )

    def _assert_totals(self, move, untaxed, tax, total):
        self.assertEqual(
            (move.amount_untaxed, move.amount_tax, move.amount_total),
            (untaxed, tax, total),
        )

    def _count_lines(self, move, display_type):
        return len(
            move.line_ids.filtered(lambda line: line.display_type == display_type)
        )

    def test_private_part_on_line_account(self):
        """100 + 21 % at 50 % on an asset (218) or an expense (628) account:
        the account carries 110.50, the deductible VAT 10.50."""
        for account_code in ("218000", "628000"):
            with self.subTest(account_code=account_code):
                bill = self._create_bill([(account_code, 100, 0.5)])
                bill.action_post()
                self._assert_balances(
                    bill, {account_code: 110.5, "472000": 10.5, "payable": -121}
                )
                self._assert_totals(bill, 100, 21, 121)

    def test_private_part_two_accounts(self):
        """Each account gets its private base and VAT: one total line per
        account and a single private tax line."""
        bill = self._create_bill([("218000", 100, 0.5), ("628000", 200, 0.5)])
        self._assert_balances(
            bill,
            {"218000": 110.5, "628000": 221, "472000": 31.5, "payable": -363},
        )
        self._assert_totals(bill, 300, 63, 363)
        self.assertEqual(self._count_lines(bill, "non_deductible_tax"), 1)
        self.assertEqual(self._count_lines(bill, "non_deductible_product_total"), 2)

    def test_private_part_edit_bill(self):
        """Editing the lines again moves the private part without duplicating
        its lines."""
        bill = self._create_bill([("218000", 100, 0.5), ("628000", 200, 0.5)])
        bill_form = Form(bill)
        with bill_form.invoice_line_ids.edit(1) as line_form:
            line_form.price_unit = 400
        bill_form.save()
        self._assert_balances(
            bill,
            {"218000": 110.5, "628000": 442, "472000": 52.5, "payable": -605},
        )
        self.assertEqual(self._count_lines(bill, "non_deductible_product_total"), 2)
        bill_form = Form(bill)
        with bill_form.invoice_line_ids.edit(0) as line_form:
            line_form.deductible_percentage = 1
        bill_form.save()
        self._assert_balances(
            bill, {"218000": 100, "628000": 442, "472000": 63, "payable": -605}
        )
        self.assertEqual(self._count_lines(bill, "non_deductible_tax"), 1)
        self.assertEqual(self._count_lines(bill, "non_deductible_product_total"), 1)

    def test_private_part_refund(self):
        """The refund made with the reversal wizard leaves the private part on
        the line account too."""
        bill = self._create_bill([("218000", 100, 0.5), ("628000", 200, 0.5)])
        bill.action_post()
        reversal = (
            self.env["account.move.reversal"]
            .with_context(active_model="account.move", active_ids=bill.ids)
            .create({"journal_id": bill.journal_id.id})
        )
        refund = self.env["account.move"].browse(reversal.refund_moves()["res_id"])
        refund.action_post()
        self._assert_balances(
            refund,
            {"218000": -110.5, "628000": -221, "472000": -31.5, "payable": 363},
        )
        self._assert_totals(refund, 300, 63, 363)

    def test_private_part_fiscal_position(self):
        """An intra-community acquisition: the reverse charge VAT is booked as
        usual and the non deductible part stays on the asset account."""
        self.partner_b.property_account_position_id = self.env[
            "account.chart.template"
        ].ref("fp_intra")
        bill = self._create_bill([("218000", 100, 0.5)], partner=self.partner_b)
        self._assert_balances(
            bill,
            {"218000": 110.5, "472000": 10.5, "477000": -21, "payable": -100},
        )

    def test_private_part_foreign_currency(self):
        """Nothing is left on the default account of the journal in a bill in
        a foreign currency either."""
        bill = self._create_bill(
            [("218000", 120, 0.5), ("628000", 120, 0.5)], currency=self.usd
        )
        self.assertEqual(
            set(bill.line_ids.account_id.mapped("code")),
            {
                "218000",
                "628000",
                "472000",
                self.partner_a.property_account_payable_id.code,
            },
        )
        self.assertAlmostEqual(sum(bill.line_ids.mapped("amount_currency")), 0)

    def test_private_part_journal_private_account(self):
        """The Private Share Account of the purchase journal (544 in the
        Spanish chart of Odoo core) doesn't take the private part, which stays
        on the account of each line, also without a Private Share Account."""
        self.assertEqual(self.journal.non_deductible_account_id.code, "544000")
        journal_without_account = self.journal.copy(
            {"code": "NOPS", "non_deductible_account_id": False}
        )
        for journal in self.journal + journal_without_account:
            with self.subTest(journal=journal.code):
                bill = self._create_bill(
                    [("218000", 100, 0.5), ("628000", 200, 0.5)], journal=journal
                )
                self._assert_balances(
                    bill,
                    {
                        "218000": 110.5,
                        "628000": 221,
                        "472000": 31.5,
                        "payable": -363,
                    },
                )

    def test_private_part_other_country(self):
        """A company of another country keeps the behaviour of Odoo core."""
        company = self.env["res.company"].create(
            {"name": "Other country", "country_id": self.env.ref("base.fr").id}
        )
        self.env.user.company_ids += company
        self.env["account.chart.template"].try_loading(
            "generic_coa", company=company, install_demo=False
        )
        self.env = self.env(
            context=dict(self.env.context, allowed_company_ids=company.ids)
        )
        journal = self.env["account.journal"].search(
            [("company_id", "=", company.id), ("type", "=", "purchase")], limit=1
        )
        asset_account = self.env["account.account"].create(
            {
                "name": "Vehicles",
                "code": "218000",
                "account_type": "asset_non_current",
                "company_ids": company.ids,
            }
        )
        bill = self._create_bill(
            [(asset_account.code, 100, 0.5)], journal=journal, partner=self.partner_a
        )
        private_lines = bill.line_ids.filtered(
            lambda line: (
                line.display_type
                in ("non_deductible_product_total", "non_deductible_tax")
            )
        )
        self.assertEqual(private_lines.account_id, journal.default_account_id)
