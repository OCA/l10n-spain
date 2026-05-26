# Copyright 2024 Binhex - Nicolás Ramos (http://binhex.es)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import fields

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.vat.book.igic")


class TestL10nEsVatBookIgic(TestL10nEsAeatModBase):
    debug = False
    taxes_sale = {
        # tax code: (base, tax_amount)
        "IGIC_R_7": (1500, 105),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "IGIC_SOP_7": (230, 16.1),
        "IGIC_SOP_I_7": (200, 14),
        "IGIC_SOP_0": (100, 0),
    }

    @classmethod
    def _chart_of_accounts_create(cls):
        """Load Canary chart so IGIC taxes exist for the company."""
        _logger.debug("Creating chart of account (Canary)")
        cls.company = cls.env["res.company"].create(
            {
                "name": "Canarias test company",
                "currency_id": cls.env.ref("base.EUR").id,
            }
        )
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        chart = cls.env["account.chart.template"]
        chart.try_loading(
            template_code="es_pymes_canary", company=cls.company, install_demo=False
        )
        cls.with_context(company_id=cls.company.id)
        return True

    def test_model_vat_book(self):
        # Purchase invoices
        self._invoice_purchase_create("2024-01-01")
        # Sale invoices
        sale = self._invoice_sale_create("2024-01-13")
        self._invoice_refund(sale, "2024-01-14")
        # Create model
        self.company.vat = "ES12345678Z"
        vat_book = self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book IGIC",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2024,
                "period_type": "1T",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
            }
        )
        _logger.debug("Calculate VAT Book 1T 2024")

        vat_book.button_calculate()
        # Check issued invoices
        for line in vat_book.issued_line_ids:
            self.assertEqual(fields.Date.to_string(line.invoice_date), "2024-01-13")
            self.assertEqual(line.partner_id, self.customer)
            for tax_line in line.tax_line_ids:
                self.assertEqual(tax_line.base_amount, 1500)
                self.assertEqual(tax_line.tax_amount, 105)
        # Check issued refund invoices
        for line in vat_book.rectification_issued_line_ids:
            self.assertEqual(fields.Date.to_string(line.invoice_date), "2024-01-14")
            self.assertEqual(line.partner_id, self.customer)
            for tax_line in line.tax_line_ids:
                self.assertEqual(tax_line.base_amount, -1500)
                self.assertEqual(tax_line.tax_amount, -105)
        # Check tax summary for issued invoices
        for line in vat_book.issued_tax_summary_ids:
            self.assertEqual(line.base_amount, 0.0)
            self.assertEqual(line.tax_amount, 0.0)
        # Check tax summary for received invoices
        self.assertEqual(len(vat_book.received_tax_summary_ids), 3)

        rec_summaries = sorted(
            vat_book.received_tax_summary_ids,
            key=lambda line: line.tax_amount,
            reverse=True,
        )
        # IGIC_SOP_7 - 7% IGIC
        line = rec_summaries[0]
        self.assertAlmostEqual(line.base_amount, 230)
        self.assertAlmostEqual(line.tax_amount, 16.1)

        # IGIC_SOP_I_7 - 7% IGIC
        line = rec_summaries[1]
        self.assertAlmostEqual(line.base_amount, 200)
        self.assertAlmostEqual(line.tax_amount, 14)

        # IGIC_SOP_0 - 0% IGIC
        line = rec_summaries[2]
        self.assertAlmostEqual(line.base_amount, 100)
        self.assertAlmostEqual(line.tax_amount, 0)

        # Print to PDF
        report_pdf = self.env["ir.actions.report"]._render(
            "l10n_es_vat_book.act_report_vat_book_invoices_issued_pdf", vat_book.ids
        )
        self.assertGreaterEqual(len(report_pdf[0]), 1)
        report_pdf = self.env["ir.actions.report"]._render(
            "l10n_es_vat_book.act_report_vat_book_invoices_received_pdf", vat_book.ids
        )
        self.assertGreaterEqual(len(report_pdf[0]), 1)
        # Export to XLSX
        report_xlsx = self.env["ir.actions.report"]._render(
            "l10n_es_vat_book.l10n_es_vat_book_xlsx", vat_book.ids
        )
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], "xlsx")
        # Check empty Vat Book
        vat_book.write(
            {
                "tax_agency_ids": [
                    (6, 0, [self.env.ref("l10n_es_aeat.aeat_tax_agency_araba").id])
                ],
            }
        )

        vat_book.button_calculate()
        self.assertEqual(len(vat_book.issued_line_ids), 0)
        self.assertEqual(len(vat_book.rectification_issued_line_ids), 0)
        self.assertEqual(len(vat_book.issued_tax_summary_ids), 0)
