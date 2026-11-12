# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging
from io import BytesIO
from typing import ClassVar

from openpyxl import load_workbook

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.vat.book.invoice.summary")


class TestL10nEsVatBookInvoiceSummary(TestL10nEsAeatModBase):
    debug = False
    taxes_sale: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "S_IVA21S": (1500, 315),
        "S_IVA10S": (100, 10),
    }

    def _summary_vals(self, start, end, **vals):
        """Summary data as the user fills them in the draft invoice."""
        return {
            "is_invoice_summary": True,
            "sii_invoice_summary_start": start,
            "sii_invoice_summary_end": end,
            **vals,
        }

    def test_model_vat_book(self):
        self._invoice_sale_create(
            "2017-01-13", extra_vals=self._summary_vals("SALE-START", "SALE-END")
        )
        normal = self._invoice_sale_create("2017-01-14")
        self._invoice_sale_create(
            "2017-01-15",
            extra_vals=self._summary_vals(
                "REFUND-START", "REFUND-END", move_type="out_refund"
            ),
        )
        # Create vat book + calculate
        # Company data are set by an administrator
        self.company.sudo().vat = "ES12345678Z"
        vat_book = self.env["l10n.es.vat.book"].create(
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
            }
        )
        vat_book.button_calculate()
        self.assertEqual(len(vat_book.issued_line_ids), 2)
        self.assertEqual(len(vat_book.rectification_issued_line_ids), 1)
        # Export to XLSX + check specific values
        action = vat_book.export_xlsx()
        report_xlsx = self.env["ir.actions.report"]._render(
            action["report_name"], vat_book.ids
        )
        # xlrd 2 no longer reads xlsx: the workbook is read with openpyxl
        wb = load_workbook(BytesIO(report_xlsx[0]))
        sheet = wb.worksheets[0]
        # Each invoice has a row per VAT rate, the total only in the first one,
        # and the range of a summary in the number columns (L and M) of all of them
        expected = [
            ("SALE-START", "SALE-END", 1925),
            ("SALE-START", "SALE-END", None),
            (normal.name, None, 1925),
            (normal.name, None, None),
            ("REFUND-START", "REFUND-END", -1925),
            ("REFUND-START", "REFUND-END", None),
        ]
        for row, (number, final_number, total) in enumerate(expected, start=8):
            self.assertEqual(sheet[f"L{row}"].value, number)
            self.assertEqual(sheet[f"M{row}"].value, final_number)
            self.assertEqual(sheet[f"U{row}"].value, total)
            # The activity columns are not touched
            self.assertIsNone(sheet[f"D{row}"].value)
            self.assertIsNone(sheet[f"E{row}"].value)
        self.assertIsNone(sheet["A14"].value)
