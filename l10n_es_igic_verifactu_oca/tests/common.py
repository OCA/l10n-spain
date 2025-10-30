# Copyright 2025 Binhex - Christian Ramos
from odoo.addons.l10n_es_verifactu_oca.tests.common import TestVerifactuCommon


class TestVerifactuIgicCommon(TestVerifactuCommon):
    """Common base class for VeriFactu tests with shared setup and utilities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.fp_nacional = cls.env.ref(f"l10n_es_igic.{cls.company.id}_fp_canary")
        cls.fp_registration_key_01 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01"
        )
        cls.fp_nacional.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_nacional.verifactu_tax_key = "03"  # IGIC"
        cls.fp_recargo = cls.env.ref(f"l10n_es_igic.{cls.company.id}_fp_recargo_canary")
        cls.fp_recargo.verifactu_registration_key = cls.fp_registration_key_01

    def _create_test_company(
        self,
        name="Test Company",
        vat="B87654321",
        verifactu_enabled=True,
    ):
        """
        Helper method to create a test company configured for verifactu.

        Args:
            name: Company name
            vat: Company VAT number (must be in valid Spanish format without country code)
            verifactu_enabled: Enable verifactu for the company
            verifactu_test: Set verifactu test mode

        Returns:
            res.company: Created company record
        """
        company = self.env["res.company"].create(
            {"name": name, "vat": vat, "country_id": self.env.ref("base.es").id}
        )
        if not company.chart_template_id:
            coa = self.env.ref(
                "l10n_es_igic.account_chart_template_pymes_canary", False
            )
            coa.try_loading(company=company, install_demo=False)
        company.write(
            {
                "verifactu_enabled": verifactu_enabled,
                "verifactu_test": True,
                "tax_agency_id": self.env.ref(
                    "l10n_es_aeat.aeat_tax_agency_canarias"
                ).id,
                "verifactu_developer_id": self.verifactu_developer.id,
            }
        )
        return company

    @classmethod
    def _chart_of_accounts_create(cls):
        cls.company = cls.env["res.company"].create(
            {"name": "Spanish test company", "currency_id": cls.env.ref("base.EUR").id}
        )
        cls.chart = cls.env.ref("l10n_es_igic.account_chart_template_pymes_canary")
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        chart = cls.env.ref("l10n_es_igic.account_chart_template_pymes_canary")
        chart.try_loading()
        cls.with_context(company_id=cls.company.id)
        return True
