# Copyright 2026 - OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command

from .common import TestVerifactuIgicCommon


class TestVerifactuIgicRepep(TestVerifactuIgicCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company.write(
            {
                "tax_agency_id": cls.env.ref(
                    "l10n_es_aeat.aeat_tax_agency_canarias"
                ).id,
                "verifactu_enabled": True,
                "verifactu_test": True,
            }
        )
        cls.tax_repep = cls.env.ref(
            f"l10n_es_igic.{cls.company.id}_account_tax_template_igic_re_ex"
        )

    def test_repep_sale_breakdown_is_e7_without_rate(self):
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "fiscal_position_id": False,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Franquicia fiscal",
                            "account_id": self.account_expense.id,
                            "price_unit": 1500,
                            "quantity": 1,
                            "tax_ids": [Command.set(self.tax_repep.ids)],
                        }
                    )
                ],
            }
        )
        self.assertEqual(invoice.verifactu_registration_key_code, "18")
        self.assertTrue(invoice._igic_repep_legend())
        taxes, _amount_tax, _amount_total = invoice._get_verifactu_taxes_and_total()
        line = taxes["DetalleDesglose"][0]
        self.assertEqual(line["Impuesto"], "03")
        self.assertEqual(line["ClaveRegimen"], "18")
        self.assertEqual(line["OperacionExenta"], "E7")
        self.assertEqual(line["BaseImponibleOimporteNoSujeto"], 1500)
        self.assertNotIn("TipoImpositivo", line)
        self.assertNotIn("CuotaRepercutida", line)
        self.assertNotIn("TipoRecargoEquivalencia", line)
        self.assertNotIn("CuotaRecargoEquivalencia", line)

    def test_lease_exemption_is_e1_not_repep(self):
        fiscal_position = self.env.ref(
            f"l10n_es_igic.{self.company.id}_fp_lease_canary"
        )
        fiscal_position.write(
            {
                "verifactu_tax_key": "03",
                "verifactu_registration_key": self.env.ref(
                    "l10n_es_verifactu_oca.verifactu_registration_keys_igic_11"
                ).id,
            }
        )
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "fiscal_position_id": fiscal_position.id,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Arrendamiento exento",
                            "account_id": self.account_expense.id,
                            "price_unit": 800,
                            "quantity": 1,
                            "tax_ids": [Command.set(self.tax_repep.ids)],
                        }
                    )
                ],
            }
        )
        self.assertEqual(invoice.verifactu_registration_key_code, "11")
        self.assertFalse(invoice._igic_repep_legend())
        taxes, _amount_tax, _amount_total = invoice._get_verifactu_taxes_and_total()
        line = taxes["DetalleDesglose"][0]
        self.assertEqual(line["OperacionExenta"], "E1")
        self.assertEqual(line["ClaveRegimen"], "11")
        self.assertEqual(line["Impuesto"], "03")
        self.assertNotIn("TipoImpositivo", line)
        self.assertNotIn("CuotaRepercutida", line)

    def test_export_sale_breakdown_is_e2_without_rate(self):
        tax = self.env.ref(
            f"l10n_es_igic.{self.company.id}_account_tax_template_igic_ex_0"
        )
        invoice = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "fiscal_position_id": False,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Exportación",
                            "account_id": self.account_expense.id,
                            "price_unit": 2500,
                            "quantity": 1,
                            "tax_ids": [Command.set(tax.ids)],
                        }
                    )
                ],
            }
        )
        self.assertEqual(invoice.verifactu_registration_key_code, "02")
        self.assertFalse(invoice._igic_repep_legend())
        taxes, _amount_tax, _amount_total = invoice._get_verifactu_taxes_and_total()
        line = taxes["DetalleDesglose"][0]
        self.assertEqual(line["Impuesto"], "03")
        self.assertEqual(line["ClaveRegimen"], "02")
        self.assertEqual(line["OperacionExenta"], "E2")
        self.assertEqual(line["BaseImponibleOimporteNoSujeto"], 2500)
        self.assertNotIn("CalificacionOperacion", line)
        self.assertNotIn("TipoImpositivo", line)
        self.assertNotIn("CuotaRepercutida", line)
        self.assertNotIn("TipoRecargoEquivalencia", line)
        self.assertNotIn("CuotaRecargoEquivalencia", line)

    def test_igic_import_surcharge_is_not_repep_key(self):
        position = self.env.ref("l10n_es_igic.fp_recargo_canary")
        self.assertEqual(position.verifactu_tax_key, "03")
        self.assertEqual(position.verifactu_registration_key.code, "01")
