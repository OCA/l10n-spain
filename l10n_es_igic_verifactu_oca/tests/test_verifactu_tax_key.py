# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command

from .common import TestVerifactuIgicCommon


class TestVerifactuTaxKey(TestVerifactuIgicCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "tax_agency_id": cls.env.ref(
                    "l10n_es_aeat.aeat_tax_agency_canarias"
                ).id,
            }
        )
        cls.igic_reg_key = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01"
        )
        cls.peninsula_reg_key = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_01"
        )

    def _create_out_invoice_vals(self, extra_vals=None):
        vals = {
            "company_id": self.company.id,
            "partner_id": self.partner.id,
            "invoice_date": "2026-01-01",
            "move_type": "out_invoice",
            "invoice_line_ids": [
                Command.create(
                    {
                        "product_id": self.product.id,
                        "account_id": self.account_expense.id,
                        "name": "Test line",
                        "price_unit": 100,
                        "quantity": 1,
                    }
                )
            ],
        }
        if extra_vals:
            vals.update(extra_vals)
        return vals

    def test_atc_invoice_without_fp_uses_igic_tax_key(self):
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": False})
        )
        self.assertEqual(invoice.verifactu_tax_key, "03")
        self.assertEqual(invoice.verifactu_registration_key, self.igic_reg_key)

    def test_atc_invoice_with_fp_without_tax_key_uses_igic(self):
        fp = self.fp_nacional.copy({"verifactu_tax_key": False})
        invoice = self.env["account.move"].create(
            self._create_out_invoice_vals({"fiscal_position_id": fp.id})
        )
        self.assertEqual(invoice.verifactu_tax_key, "03")

    def test_atc_fiscal_position_default_tax_key_on_create(self):
        fp = self.env["account.fiscal.position"].create(
            {
                "name": "ATC test FP",
                "company_id": self.company.id,
            }
        )
        self.assertEqual(fp.verifactu_tax_key, "03")

    def test_peninsula_company_keeps_iva_tax_key(self):
        spain_agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_spain")
        original_agency = self.company.tax_agency_id
        self.company.tax_agency_id = spain_agency
        try:
            invoice = self.env["account.move"].create(
                self._create_out_invoice_vals({"fiscal_position_id": False})
            )
            self.assertEqual(invoice.verifactu_tax_key, "01")
            self.assertEqual(invoice.verifactu_registration_key, self.peninsula_reg_key)
        finally:
            self.company.tax_agency_id = original_agency
