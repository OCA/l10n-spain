# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from io import BytesIO
from typing import ClassVar

from openpyxl import load_workbook

from odoo.fields import Command

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
