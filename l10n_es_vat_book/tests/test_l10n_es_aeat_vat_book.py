# Copyright 2017 ForgeFlow, S.L.
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import logging

from odoo import fields

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.vat.book")


class TestL10nEsAeatVatBook(TestL10nEsAeatModBase):
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21S": (1500, 315),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA21_SC": (230, 48.3),
        "P_IVA0_ND": (100, 21),
        "P_IVA21_IC_BC": (200, 42),
    }

    def test_model_vat_book(self):
        # Purchase invoices
        self._invoice_purchase_create("2017-01-01")
        # Sale invoices
        sale = self._invoice_sale_create("2017-01-13")
        self._invoice_refund(sale, "2017-01-14")
        # Create model
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
        _logger.debug("Calculate VAT Book 1T 2017")
        vat_book.button_calculate()
        # Check issued invoices
        for line in vat_book.issued_line_ids:
            self.assertEqual(fields.Date.to_string(line.invoice_date), "2017-01-13")
            self.assertEqual(line.partner_id, self.customer)
            for tax_line in line.tax_line_ids:
                self.assertEqual(tax_line.base_amount, 1500)
                self.assertEqual(tax_line.tax_amount, 315)
        # Check issued refund invoices
        for line in vat_book.rectification_issued_line_ids:
            self.assertEqual(fields.Date.to_string(line.invoice_date), "2017-01-14")
            self.assertEqual(line.partner_id, self.customer)
            for tax_line in line.tax_line_ids:
                self.assertEqual(tax_line.base_amount, -1500)
                self.assertEqual(tax_line.tax_amount, -315)
        # Check tax summary for issued invoices
        for line in vat_book.issued_tax_summary_ids:
            self.assertEqual(line.base_amount, 0.0)
            self.assertEqual(line.tax_amount, 0.0)
        # Check tax summary for received invoices
        self.assertEqual(len(vat_book.received_tax_summary_ids), 3)
        # P_IVA21_SC - 21% IVA soportado (servicios corrientes)
        line = vat_book.received_tax_summary_ids[0]
        self.assertAlmostEqual(line.base_amount, 230)
        self.assertAlmostEqual(line.tax_amount, 48.3)
        # P_IVA21_IC_BC - IVA 21% Adquisición Intracomunitaria. Bienes corrientes
        line = vat_book.received_tax_summary_ids[1]
        self.assertAlmostEqual(line.base_amount, 200)
        self.assertAlmostEqual(line.tax_amount, 42)
        # P_IVA0_ND - 21% IVA Soportado no deducible
        line = vat_book.received_tax_summary_ids[2]
        self.assertAlmostEqual(line.base_amount, 100)
        self.assertAlmostEqual(line.tax_amount, 21)
        # Print to PDF
        report_pdf = self.env.ref(
            "l10n_es_vat_book.act_report_vat_book_invoices_issued_pdf"
        ).render(vat_book.ids)
        self.assertGreaterEqual(len(report_pdf[0]), 1)
        report_pdf = self.env.ref(
            "l10n_es_vat_book.act_report_vat_book_invoices_received_pdf"
        ).render(vat_book.ids)
        self.assertGreaterEqual(len(report_pdf[0]), 1)
        # Export to XLSX
        report_name = "l10n_es_vat_book.l10n_es_vat_book_xlsx"
        report_xlsx = self.env.ref(report_name).render(vat_book.ids)
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], "xlsx")
