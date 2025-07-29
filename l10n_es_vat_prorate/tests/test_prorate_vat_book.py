from datetime import date

from odoo.tests.common import tagged

from odoo.addons.l10n_es_vat_book.tests import test_l10n_es_aeat_vat_book


@tagged("-at_install", "post_install")
class TestSIIVatProrate(test_l10n_es_aeat_vat_book.TestL10nEsAeatVatBookBase):
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA21_SC": (200, 42),
    }

    @classmethod
    def setUpClass(cls):
        try:
            super().setUpClass()
        except Exception:
            cls.skipTest(cls, "l10n_es_aeat_vat_book seems not installed")
        cls.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    (0, 0, {"date": date(2025, 1, 1), "vat_prorate": 20}),
                ],
            }
        )

    def test_get_invoice_data(self):
        # Purchase invoices
        self._invoice_purchase_create("2025-01-01")
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
                "year": 2025,
                "period_type": "1T",
                "date_start": "2025-01-01",
                "date_end": "2025-03-31",
            }
        )
        vat_book.button_calculate()
        # P_IVA21_SC - 21% IVA soportado (servicios corrientes)
        line = vat_book.received_line_ids[0]
        self.assertAlmostEqual(line.tax_line_ids.base_amount, 200)
        self.assertAlmostEqual(line.tax_line_ids.tax_amount, 42)
        self.assertAlmostEqual(line.tax_line_ids.deductible_amount, 8.4)
