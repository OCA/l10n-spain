# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from xlrd import open_workbook

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.vat.book.invoice.summary")


class TestL10nEsVatBookInvoiceSummary(TestL10nEsAeatModBase):
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21S": (1500, 315),
    }

    def test_model_vat_book(self):
        # Sale invoices with invoice summary
        sale = self._invoice_sale_create("2017-01-13")
        sale.is_invoice_summary = True
        sale.sii_invoice_summary_start = "SALE-START"
        sale.sii_invoice_summary_end = "SALE-END"
        # Create vat boo + calculate
        self.company.vat = "ES12345678Z"
        vat_book = self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book",
                "company_id": self.company.id,
                "company_vat": "1234567890",
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
        # Export to XLSX + check specific values
        report_name = "l10n_es_vat_book.l10n_es_vat_book_xlsx"
        report_xlsx = self.env["ir.actions.report"]._render(report_name, vat_book.ids)
        wb = open_workbook(file_contents=report_xlsx[0])
        sheet = wb.sheet_by_index(0)
        self.assertEqual(sheet.cell(7, 3).value, "SALE-START")
        self.assertEqual(sheet.cell(7, 4).value, "SALE-END")
