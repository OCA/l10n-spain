# Copyright 2025 Binhex - Christian Ramos
from odoo import Command

from odoo.addons.l10n_es_verifactu_oca.tests.common import TestVerifactuCommon


class TestVerifactuIgicCommon(TestVerifactuCommon):
    """Common base class for VeriFactu IGIC tests with Canary chart."""

    @classmethod
    def _chart_of_accounts_create(cls):
        project = cls.env["project.project"]
        if "billing_type" in project._fields:

            def create_with_billing_type(self, vals_list):
                for vals in vals_list:
                    vals.setdefault("billing_type", "not_billable")
                return create_with_billing_type.origin(self, vals_list)

            project._patch_method("create", create_with_billing_type)
            cls.addClassCleanup(project._revert_method, "create")
        cls.company = cls.env["res.company"].create(
            {
                "name": "Spanish test company",
                "currency_id": cls.env.ref("base.EUR").id,
            }
        )
        cls.env.ref("base.group_multi_company").write({"users": [(4, cls.env.uid)]})
        cls.env.user.write(
            {"company_ids": [(4, cls.company.id)], "company_id": cls.company.id}
        )
        cls.env["account.chart.template"].try_loading(
            "es_canary_pymes", company=cls.company, install_demo=False
        )
        cls.with_context(company_id=cls.company.id)
        return True

    @classmethod
    def setUpClass(cls):
        super(TestVerifactuCommon, cls).setUpClass()
        cls.maxDiff = None
        cls._saved_verifactu_company_states = {
            company.id: True
            for company in cls.env["res.company"]
            .sudo()
            .search(
                [
                    ("verifactu_enabled", "=", True),
                    ("id", "!=", cls.company.id),
                ]
            )
        }
        if cls._saved_verifactu_company_states:
            cls.env["res.company"].browse(
                list(cls._saved_verifactu_company_states)
            ).sudo().write({"verifactu_enabled": False})
        cls.fp_nacional = cls.env.ref(f"account.{cls.company.id}_fp_canary_1")
        cls.fp_registration_key_01 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_01"
        )
        cls.fp_registration_key_17 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_17"
        )
        cls.fp_nacional.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_nacional.verifactu_tax_key = "03"
        cls.fp_recargo = cls.env.ref(f"account.{cls.company.id}_fp_recargo_canary")
        cls.fp_recargo.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_extra = cls.env.ref(f"account.{cls.company.id}_fp_extra_canary")
        cls.fp_extra.verifactu_registration_key = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_igic_02"
        )
        cls.fp_retailer = cls.env.ref(f"account.{cls.company.id}_fp_retailer_canary")
        cls.fp_retailer.verifactu_tax_key = "03"
        cls.fp_retailer.verifactu_registration_key = cls.fp_registration_key_17
        cls.tax_igic_r_7 = cls.env.ref(
            f"account.{cls.company.id}_account_tax_template_igic_r_7"
        )
        cls.tax_igic_r_3 = cls.env.ref(
            f"account.{cls.company.id}_account_tax_template_igic_r_3"
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "vat": "89890001K",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.product.taxes_id = [(6, 0, [cls.tax_igic_r_7.id])]
        cls.account_expense = cls.env.ref(
            f"account.{cls.company.id}_account_common_600",
            raise_if_not_found=False,
        )
        if not cls.account_expense:
            cls.account_expense = cls.env["account.account"].search(
                [
                    ("company_ids", "=", cls.company.id),
                    ("account_type", "=", "expense"),
                ],
                limit=1,
            )
        cls.verifactu_developer = cls.env["verifactu.developer"].create(
            {
                "name": "Odoo Developer",
                "vat": "A12345674",
                "sif_name": "odoo",
                "version": "1.0",
            }
        )
        cls.verifactu_chaining = cls.env["verifactu.chaining"].create(
            {"name": "VERI*FACTU Chaining", "sif_id": "11", "installation_number": 1}
        )
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
                        }
                    )
                ],
            }
        )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "_saved_verifactu_company_states", None):
            cls.env["res.company"].browse(
                list(cls._saved_verifactu_company_states)
            ).sudo().write({"verifactu_enabled": True})
        super().tearDownClass()

    def _create_test_company(
        self,
        name="Test Company",
        vat="B87654321",
        verifactu_enabled=True,
    ):
        company = self.env["res.company"].create(
            {"name": name, "vat": vat, "country_id": self.env.ref("base.es").id}
        )
        if not company.chart_template:
            self.env["account.chart.template"].try_loading(
                "es_canary_pymes", company=company, install_demo=False
            )
        canary_agency = self.env.ref("l10n_es_aeat.aeat_tax_agency_canarias")
        company.write(
            {
                "verifactu_enabled": verifactu_enabled,
                "verifactu_test": True,
                "tax_agency_id": canary_agency.id,
                "verifactu_developer_id": self.verifactu_developer.id,
            }
        )
        return company
