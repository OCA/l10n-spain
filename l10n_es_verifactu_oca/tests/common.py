# Copyright 2024 FactorLibre - Luis J. Salvatierra
# Copyright 2025 Tecnativa - Pedro M. Baeza
from odoo import Command, fields

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_certificate import (
    TestL10nEsAeatCertificateBase,
)
from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestVerifactuCommon(TestL10nEsAeatModBase, TestL10nEsAeatCertificateBase):
    """Common base class for VeriFactu tests with shared setup and utilities."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.maxDiff = None
        cls.fp_nacional = cls.env.ref(f"account.{cls.company.id}_fp_nacional")
        cls.fp_registration_key_01 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_01"
        )
        cls.fp_registration_key_02 = cls.env.ref(
            "l10n_es_verifactu_oca.verifactu_registration_keys_02"
        )
        cls.fp_nacional.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_recargo = cls.env.ref(f"account.{cls.company.id}_fp_recargo")
        cls.fp_recargo.verifactu_registration_key = cls.fp_registration_key_01
        cls.fp_extra = cls.env.ref(f"account.{cls.company.id}_fp_extra")
        cls.fp_extra.verifactu_registration_key = cls.fp_registration_key_02
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Test partner",
                "vat": "89890001K",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.account_expense = cls.env.ref(
            f"account.{cls.company.id}_account_common_600"
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
                "tax_agency_id": cls.env.ref("l10n_es_aeat.aeat_tax_agency_spain"),
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

    def _create_test_invoice(
        self,
        company=None,
        date="2024-01-01",
        amount=100,
        partner=None,
        move_type="out_invoice",
        product=None,
        account=None,
        name=None,
    ):
        """
        Helper method to create a test invoice with customizable parameters.

        Args:
            company: Company for the invoice (defaults to self.company)
            date: Invoice date (defaults to "2024-01-01")
            amount: Invoice line amount (defaults to 100)
            partner: Invoice partner (defaults to self.partner)
            move_type: Invoice type (defaults to "out_invoice")
            product: Product for invoice line (defaults to self.product)
            account: Account for invoice line (defaults to self.account_expense)
            name: Invoice line description (defaults to "Test line")

        Returns:
            account.move: Created invoice record
        """
        company = company or self.company
        partner = partner or self.partner
        product = product or self.product
        if account is None:
            if company == self.company:
                account = self.account_expense
            else:
                account = self.env["account.account"].search(
                    [
                        ("company_ids", "=", company.id),
                        ("account_type", "=", "expense"),
                    ],
                    limit=1,
                )
                if not account:
                    account = self.env["account.account"].search(
                        [("company_ids", "=", company.id)], limit=1
                    )
        if name is None:
            name = f"Test line - {amount}"
        return self.env["account.move"].create(
            {
                "company_id": company.id,
                "partner_id": partner.id,
                "invoice_date": date,
                "move_type": move_type,
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": product.id,
                            "account_id": account.id,
                            "name": name,
                            "price_unit": amount,
                            "quantity": 1,
                        },
                    )
                ],
                "aeat_state": "sent",
            }
        )

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
            vat: Company VAT number (must be in valid Spanish format without country
                code)
            verifactu_enabled: Enable verifactu for the company
            verifactu_test: Set verifactu test mode

        Returns:
            res.company: Created company record
        """
        company = self.env["res.company"].create(
            {"name": name, "vat": vat, "country_id": self.env.ref("base.es").id}
        )
        if not company.chart_template:
            chart = self.env["account.chart.template"]
            chart._load(template_code="es_pymes", company=company, install_demo=False)
        company.write(
            {
                "verifactu_enabled": verifactu_enabled,
                "verifactu_test": True,
                "tax_agency_id": self.env.ref("l10n_es_aeat.aeat_tax_agency_spain").id,
                "verifactu_developer_id": self.verifactu_developer.id,
            }
        )
        return company

    def _prepare_invoice_for_verifactu(self, invoice):
        """
        Helper method to prepare an invoice for verifactu processing.
        This includes posting the invoice and setting the registration date.

        Args:
            invoice: Invoice to prepare

        Returns:
            account.move: The prepared invoice
        """
        invoice.action_post()
        invoice.verifactu_registration_date = fields.Datetime.now()
        return invoice

    def _create_and_prepare_invoice(self, **kwargs):
        """
        Helper method to create and prepare an invoice for verifactu in one step.

        Args:
            **kwargs: Arguments passed to _create_test_invoice

        Returns:
            account.move: Created and prepared invoice
        """
        invoice = self._create_test_invoice(**kwargs)
        return self._prepare_invoice_for_verifactu(invoice)

    def _verify_queue_creation(self, invoice):
        """
        Helper method to verify that a queue record was created for an invoice.

        Args:
            invoice: Invoice to verify queue creation for

        Returns:
            verifactu.invoice.entry: The created queue record
        """
        entry = invoice.last_verifactu_invoice_entry_id
        self.assertTrue(
            entry,
            "Invoice should have a VERI*FACTU invoice entry after posting",
        )
        response_lines = entry.response_line_ids
        self.assertEqual(len(response_lines), 1, "Should have exactly one queue record")
        response_line = response_lines[-1]
        self.assertEqual(
            response_line.entry_id,
            entry,
            "Queue record should link to the VERI*FACTU invoice entry",
        )
        self.assertEqual(
            response_line.company_id,
            invoice.company_id,
            "Queue record should belong to the same company",
        )
        return response_line

    def _verify_response_integration(self, invoice, response_line):
        """
        Helper method to verify response line integration with verifactu.invoice.

        Args:
            invoice: Original invoice
            response_line: Response line to verify

        Returns:
            bool: True if integration is correct
        """
        self.assertTrue(
            response_line.document_id,
            "Response line should have verifactu invoice reference",
        )
        self.assertEqual(
            response_line.entry_id,
            invoice.last_verifactu_invoice_entry_id,
            "Response line should link to the correct VERI*FACTU invoice entry",
        )
        self.assertEqual(
            response_line.entry_id.document_id,
            invoice,
            "Response line should reference the original invoice through verifactu "
            "entry",
        )
        return True

    def _generate_invoice_entry(self, invoice):
        """
        Helper method to generate VERI*FACTU invoice entry for an invoice.
        This assumes the invoice is already prepared for verifactu.

        Args:
            invoice: Prepared invoice

        Returns:
            verifactu.invoice: Created invoice entry
        """
        invoice._generate_verifactu_chaining()
        return invoice.last_verifactu_invoice_entry_id


class TestVerifactuIgicCommon(TestVerifactuCommon):
    """Common base class for VeriFactu IGIC tests with Canary chart."""

    @classmethod
    def _chart_of_accounts_create(cls):
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
