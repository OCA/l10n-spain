# Copyright 2022 CreuBlanca
# Copyright 2022 Eric Antones <eantones@nuobit.com>
# Copyright 2024 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from odoo.tests import Form

from .common import TestL10nEsAeatModBase

_logger = logging.getLogger("aeat")


class TestL10nEsAeatTaxInfo(TestL10nEsAeatModBase):
    taxes_sale = {  # noqa: RUF012
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 0),
    }

    def test_tax_info_21B(self):
        invoice = self._invoice_sale_create("2024-02-01", {})
        tax_info = invoice._get_aeat_tax_info()
        tax = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax]["base"], 1000)
        self.assertEqual(tax_info[tax]["amount"], 210)

    def test_tax_info_refund_21B(self):
        invoice = self._invoice_sale_create("2024-02-01", {})
        refund = invoice._reverse_moves()
        tax_info = refund._get_aeat_tax_info()
        tax = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax]["base"], -1000)
        self.assertEqual(tax_info[tax]["amount"], -210)


class TestL10nEsAeatTaxInfoGroup(TestL10nEsAeatModBase):
    taxes_sale = {  # noqa: RUF012
        # tax code: (base, tax_amount)
        "S_IVAG1021B": (1000, 0),
    }

    @classmethod
    def _chart_of_accounts_create(cls):
        res = super()._chart_of_accounts_create()
        iva10b = cls.env.ref(f"account.{cls.company.id}_account_tax_template_s_iva10b")
        iva21b = cls.env.ref(f"account.{cls.company.id}_account_tax_template_s_iva21b")
        cls.env["account.tax"]._load_records(
            [
                {
                    "xml_id": (
                        f"account.{cls.company.id}_account_tax_template_s_ivag1021b"
                    ),
                    "noupdate": True,
                    "values": {
                        "type_tax_use": "sale",
                        "name": "Grupo IVA 10%/21% (Bienes)",
                        "amount_type": "group",
                        "tax_scope": "consu",
                        "children_tax_ids": [(6, 0, [iva10b.id, iva21b.id])],
                    },
                }
            ]
        )
        return res

    def test_tax_info_1021B(self):
        invoice = self._invoice_sale_create("2024-02-01", {})
        tax_info = invoice._get_aeat_tax_info()
        tax10 = self._get_taxes("S_IVA10B")[0]
        tax21 = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax10]["base"], 1000)
        self.assertEqual(tax_info[tax10]["amount"], 100)
        self.assertEqual(tax_info[tax21]["base"], 1000)
        self.assertEqual(tax_info[tax21]["amount"], 210)

    def test_tax_info_refund_1021B(self):
        invoice = self._invoice_sale_create("2024-02-01", {})
        refund = invoice._reverse_moves()
        tax_info = refund._get_aeat_tax_info()
        tax10 = self._get_taxes("S_IVA10B")[0]
        tax21 = self._get_taxes("S_IVA21B")[0]
        self.assertEqual(tax_info[tax10]["base"], -1000)
        self.assertEqual(tax_info[tax10]["amount"], -100)
        self.assertEqual(tax_info[tax21]["base"], -1000)
        self.assertEqual(tax_info[tax21]["amount"], -210)


class TestL10nEsAeatTaxInfoNonDeductible(TestL10nEsAeatModBase):
    """A vendor bill line with a deductible percentage (arts. 95 and 96 LIVA,
    e.g. a car used 50 % in the activity): the invoice is declared as issued,
    with the whole base and quota, and only the deductible part of the quota as
    deductible (AEAT SII FAQ 4.16, example 7)."""

    def _create_bill(self, lines):
        bill_form = Form(
            self.env["account.move"]
            .with_user(self.billing_user)
            .with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = self.supplier
        bill_form.invoice_date = "2024-01-15"
        bill_form.journal_id = self.journal_purchase
        for price_unit, tax_code, deductible_percentage in lines:
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.name = "Mixed use expense"
                line_form.price_unit = price_unit
                line_form.tax_ids.clear()
                line_form.tax_ids.add(self._get_taxes(tax_code))
                line_form.deductible_percentage = deductible_percentage
        bill = bill_form.save()
        bill.action_post()
        return bill

    def _assert_tax_info(self, move, expected):
        tax_info = move._get_aeat_tax_info()
        self.assertEqual(
            {
                tax: tuple(
                    round(vals[key], 2)
                    for key in ("base", "amount", "deductible_amount")
                )
                for tax, vals in tax_info.items()
            },
            {
                self._get_taxes(tax_code): values
                for tax_code, values in expected.items()
            },
        )

    def test_tax_info_non_deductible(self):
        """100 + 21 % at 50 %: base 100, quota 21, deductible quota 10.50."""
        bill = self._create_bill([(100, "P_IVA21_BC", 0.5)])
        self._assert_tax_info(bill, {"P_IVA21_BC": (100, 21, 10.5)})

    def test_tax_info_non_deductible_refund(self):
        """The refund of the bill gives the same amounts with the sign changed."""
        bill = self._create_bill([(100, "P_IVA21_BC", 0.5)])
        reversal = (
            self.env["account.move.reversal"]
            .with_user(self.billing_user)
            .with_context(active_model="account.move", active_ids=bill.ids)
            .create({"journal_id": bill.journal_id.id})
        )
        refund = self.env["account.move"].browse(reversal.refund_moves()["res_id"])
        refund.action_post()
        self._assert_tax_info(refund, {"P_IVA21_BC": (-100, -21, -10.5)})

    def test_tax_info_non_deductible_two_taxes(self):
        """Odoo core books the private part of both taxes on one line: each tax
        gets its own part, also the 10 % one, which is not a tax of the expense
        account."""
        bill = self._create_bill(
            [(100, "P_IVA21_BC", 0.5), (200, "P_IVA10_BC", 0.2), (300, "P_IVA21_BC", 1)]
        )
        self._assert_tax_info(
            bill,
            {"P_IVA21_BC": (400, 84, 73.5), "P_IVA10_BC": (200, 20, 4)},
        )
