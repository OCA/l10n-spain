# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from io import BytesIO
from typing import ClassVar

from openpyxl import load_workbook

from odoo.fields import Command, Datetime
from odoo.tests import Form

from .test_l10n_es_aeat_vat_book import TestL10nEsAeatVatBookBase


class TestL10nEsVatBookXlsx(TestL10nEsAeatVatBookBase):
    """Content of the book exported in the AEAT XLSX format."""

    taxes_sale: ClassVar[dict] = {
        "S_IVA21B,S_REQ52": (1000, 262),
        "S_IVA10B": (500, 50),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Company data are set by an administrator
        cls.company.sudo().vat = "ES12345678Z"
        cls.customer.vat = "ES12345678Z"
        cls.supplier.vat = "ES87654321X"

    def _purchase_create(self, invoice_date, taxes, base, **extra_vals):
        """Supplier bill with one line of the given tax, posted by the billing user."""
        if isinstance(taxes, str):
            taxes = self._get_taxes(taxes)
        bill = (
            self.env["account.move"]
            .with_user(self.billing_user)
            .create(
                {
                    "company_id": self.company.id,
                    "partner_id": self.supplier.id,
                    "invoice_date": invoice_date,
                    "move_type": "in_invoice",
                    "journal_id": self.journal_purchase.id,
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": f"Test for tax {taxes.name}",
                                "account_id": self.accounts["600000"].id,
                                "price_unit": base,
                                "quantity": 1,
                                "tax_ids": [Command.set(taxes.ids)],
                            }
                        )
                    ],
                    **extra_vals,
                }
            )
        )
        bill.action_post()
        return bill

    def _create_vat_book(self, **vals):
        return self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
                **vals,
            }
        )

    def _export_xlsx(self, vat_book):
        action = vat_book.export_xlsx()
        content, report_type = self.env["ir.actions.report"]._render(
            action["report_name"], vat_book.ids
        )
        self.assertEqual(report_type, "xlsx")
        workbook = load_workbook(BytesIO(content))
        return workbook.worksheets[0], workbook.worksheets[1]

    def _rows(self, sheet, key_column):
        """Rows of book lines (from the 8th) indexed by the value of a column."""
        return {
            sheet[f"{key_column}{row}"].value: row
            for row in range(8, sheet.max_row + 1)
            if sheet[f"A{row}"].value
        }

    def test_xlsx_issued(self):
        self._invoice_sale_create("2017-01-13")
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        vat_book.button_confirm()
        issued, _received = self._export_xlsx(vat_book)
        rows = self._rows(issued, "W")
        self.assertEqual(len(rows), 2)
        row21, row10 = rows[21], rows[10]
        # Total of the invoice only in its first row
        self.assertEqual(issued[f"U{min(rows.values())}"].value, 1812)
        self.assertIsNone(issued[f"U{max(rows.values())}"].value)
        self.assertEqual(issued[f"V{row21}"].value, 1000)
        self.assertEqual(issued[f"X{row21}"].value, 210)
        # The surcharge goes in the row of its VAT
        self.assertEqual(issued[f"Y{row21}"].value, 5.2)
        self.assertEqual(issued[f"Z{row21}"].value, 52)
        self.assertEqual(issued[f"V{row10}"].value, 500)
        self.assertEqual(issued[f"X{row10}"].value, 50)
        self.assertIsNone(issued[f"Y{row10}"].value)
        self.assertEqual(issued[f"P{row21}"].value, "12345678Z")

    def test_xlsx_surcharge_columns_follow_map(self):
        """The columns of the special taxes are read from the editable map."""
        self._invoice_sale_create("2017-01-13")
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        issued, _received = self._export_xlsx(vat_book)
        row21 = self._rows(issued, "W")[21]
        self.assertEqual(issued[f"Z{row21}"].value, 52)
        self.env.ref("l10n_es_vat_book.aeat_vat_book_map_line_s_req").write(
            {"fee_type_xlsx_column": "AG", "fee_amount_xlsx_column": "AH"}
        )
        issued, _received = self._export_xlsx(vat_book)
        self.assertEqual(issued[f"AG{row21}"].value, 5.2)
        self.assertEqual(issued[f"AH{row21}"].value, 52)
        self.assertIsNone(issued[f"Z{row21}"].value)

    def test_xlsx_received(self):
        # Accounting date in the next month
        self._purchase_create("2017-01-20", "P_IVA21_BC", 100, date="2017-02-03")
        self._purchase_create("2017-01-21", "P_IVA0_ND", 200, date="2017-01-21")
        # Reverse charge: the -21 % line of the 477 account stays out
        self._purchase_create("2017-01-22", "P_IVA21_ISP", 300)
        self._purchase_create("2017-01-23", "P_IVA21_SP_IN", 400)
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        vat_book.button_confirm()
        _issued, received = self._export_xlsx(vat_book)
        rows = self._rows(received, "AA")
        self.assertEqual(len(rows), 4)
        row_bc, row_nd, row_isp, row_sp = (rows[base] for base in (100, 200, 300, 400))
        self.assertEqual(
            received[f"J{row_bc}"].value, Datetime.to_datetime("2017-02-03")
        )
        self.assertEqual(received[f"Y{row_bc}"].value, "02")
        self.assertEqual(received[f"AC{row_bc}"].value, 21)
        self.assertEqual(received[f"AD{row_bc}"].value, 21)
        self.assertIsNone(received[f"J{row_nd}"].value)
        self.assertEqual(received[f"Y{row_nd}"].value, "01")
        self.assertEqual(received[f"AC{row_nd}"].value, 42)
        self.assertIsNone(received[f"AD{row_nd}"].value)
        for row, total, amount in ((row_isp, 363, 63), (row_sp, 484, 84)):
            self.assertEqual(received[f"Z{row}"].value, total)
            self.assertEqual(received[f"AC{row}"].value, amount)
            self.assertEqual(received[f"AD{row}"].value, amount)
        vat_book.vat_settlement_period = "quarterly"
        _issued, received = self._export_xlsx(vat_book)
        self.assertEqual(received[f"Y{row_bc}"].value, "1T")

    def test_xlsx_not_deductible_by_tax_type(self):
        """A tax typed as not deductible has no deductible quota in the book."""
        tax = self._get_taxes("P_IVA21_BC").copy()
        tax.l10n_es_type = "no_deducible"
        self._purchase_create("2017-01-20", tax, 100)
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        _issued, received = self._export_xlsx(vat_book)
        row = self._rows(received, "AA")[100]
        self.assertEqual(received[f"AC{row}"].value, 21)
        self.assertIsNone(received[f"AD{row}"].value)

    def test_xlsx_received_deductible_percentage(self):
        """A bill line of 100 + 21 % VAT with a deductible percentage of 50 %
        (art. 95 LIVA) is booked as the invoice was received: base 100 and quota
        21 (art. 64.4 RIVA), with a deductible quota of 10.50. The lines Odoo core
        adds for the private part are not another base nor lose the quota.
        """
        bill_form = Form(
            self.env["account.move"]
            .with_user(self.billing_user)
            .with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = self.supplier
        bill_form.invoice_date = "2017-01-20"
        bill_form.journal_id = self.journal_purchase
        with bill_form.invoice_line_ids.new() as line_form:
            line_form.name = "Mixed use car"
            line_form.price_unit = 100
            line_form.tax_ids.clear()
            line_form.tax_ids.add(self._get_taxes("P_IVA21_BC"))
            line_form.deductible_percentage = 0.5
        bill = bill_form.save()
        bill.action_post()
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        book_line = vat_book.received_line_ids
        self.assertEqual(book_line.move_id, bill)
        self.assertAlmostEqual(book_line.base_amount, 100, 2)
        self.assertAlmostEqual(book_line.total_amount, 121, 2)
        tax_line = book_line.tax_line_ids
        self.assertEqual(tax_line.tax_id, self._get_taxes("P_IVA21_BC"))
        self.assertAlmostEqual(tax_line.base_amount, 100, 2)
        self.assertAlmostEqual(tax_line.tax_amount, 21, 2)
        self.assertAlmostEqual(tax_line.deductible_amount, 10.5, 2)
        summary = vat_book.received_tax_summary_ids
        self.assertAlmostEqual(summary.base_amount, 100, 2)
        self.assertAlmostEqual(summary.tax_amount, 21, 2)
        _issued, received = self._export_xlsx(vat_book)
        rows = self._rows(received, "AA")
        self.assertEqual(list(rows), [100])
        row = rows[100]
        self.assertEqual(received[f"Z{row}"].value, 121)
        self.assertEqual(received[f"AC{row}"].value, 21)
        self.assertEqual(received[f"AD{row}"].value, 10.5)
        # Its credit note is booked with the same amounts, as a rectification
        self._invoice_refund(bill, "2017-01-25")
        vat_book.button_calculate()
        tax_line = vat_book.rectification_received_line_ids.tax_line_ids
        self.assertAlmostEqual(tax_line.base_amount, -100, 2)
        self.assertAlmostEqual(tax_line.tax_amount, -21, 2)
        self.assertAlmostEqual(tax_line.deductible_amount, -10.5, 2)
