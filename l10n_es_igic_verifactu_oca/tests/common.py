# Copyright 2025 Binhex - Christian Ramos

from odoo import Command

from odoo.addons.l10n_es_verifactu_oca.tests.common import TestVerifactuCommon


class TestVerifactuIgicCommon(TestVerifactuCommon):
    """Common base class for VeriFactu tests with shared setup and utilities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        chart = cls.env["account.chart.template"]
        chart._load(
            template_code="es_canary_pymes", company=cls.company, install_demo=False
        )

        cls.account_expense = cls.env.ref(
            f"account.{cls.company.id}_account_common_600"
        )

        cls.fp_registration_key_01 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01"
        )

        cls.fp_canary = cls.env.ref(f"account.{cls.company.id}_fp_canary_1")
        cls.fp_canary.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_canary.verifactu_tax_key = "03"  # IGIC
        cls.fp_recargo = cls.env.ref(f"account.{cls.company.id}_fp_recargo_canary")
        cls.fp_recargo.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_recargo.verifactu_tax_key = "03"

        cls.company.write(
            {
                "verifactu_enabled": True,
                "verifactu_test": True,
                "vat": "G87846952",
                "country_id": cls.env.ref("base.es").id,
                "tax_agency_id": cls.env.ref(
                    "l10n_es_aeat.aeat_tax_agency_canarias"
                ).id,
                "verifactu_developer_id": cls.verifactu_developer.id,
                "verifactu_chaining_id": cls.verifactu_chaining.id,
            }
        )
        cls.invoice = cls.env["account.move"].create(
            {
                "company_id": cls.company.id,
                "partner_id": cls.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": cls.product.id,
                            "account_id": cls.account_expense.id,
                            "name": "Test line",
                            "price_unit": 100,
                            "quantity": 1,
                        },
                    )
                ],
            }
        )
