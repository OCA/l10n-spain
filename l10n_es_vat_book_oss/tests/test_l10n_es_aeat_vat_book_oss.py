# Copyright 2024 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.l10n_es_vat_book.tests.test_l10n_es_aeat_vat_book import (
    TestL10nEsAeatVatBook,
)


class TestL10nEsAeatVatBookOss(TestL10nEsAeatVatBook):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.belgium_customer = cls.env["res.partner"].create(
            {
                "company_id": cls.company.id,
                "name": "Test customer Belgium",
                "country_id": cls.env.ref("base.be").id,
            }
        )
        cls.portugal_customer = cls.env["res.partner"].create(
            {
                "company_id": cls.company.id,
                "name": "Test customer Portugal",
                "country_id": cls.env.ref("base.pt").id,
            }
        )
        cls.spain_customer = cls.env["res.partner"].create(
            {
                "company_id": cls.company.id,
                "name": "Test customer Spain",
                "country_id": cls.env.ref("base.es").id,
            }
        )
        cls.company.write({"vat": "1234567890"})

    def test_model_vat_book_oss(self):
        sp_fiscal_position = self.env.ref(
            "l10n_es.{}_fp_nacional".format(self.company.id)
        )
        general_tax = self.env.ref(
            "l10n_es.{}_account_tax_template_s_iva21b".format(self.company.id)
        )
        wizard_vals = {
            "company_id": self.company.id,
            "general_tax": general_tax.id,
        }
        wizard = self.env["l10n.eu.oss.wizard"].create(wizard_vals)
        wizard.todo_country_ids = [
            (6, 0, [self.env.ref("base.be").id, self.env.ref("base.pt").id])
        ]
        wizard.generate_eu_oss_taxes()

        # Invoice for Spanish customer
        data = {
            "company_id": self.company.id,
            "partner_id": self.spain_customer.id,
            "move_type": "out_invoice",
            "journal_id": self.journal_sale.id,
            "fiscal_position_id": sp_fiscal_position.id,
            "invoice_date": "2024-01-01",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Test SP Tax",
                        "account_id": self.accounts["700000"].id,
                        "price_unit": 10,
                        "quantity": 1,
                    },
                )
            ],
        }
        inv_es = self.env["account.move"].with_company(self.company).create(data)
        inv_es.action_post()

        # Customer Invoice for Belgian customer
        data = {
            "company_id": self.company.id,
            "partner_id": self.belgium_customer.id,
            "move_type": "out_invoice",
            "journal_id": self.journal_sale.id,
            "invoice_date": "2024-01-01",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Test BE Tax",
                        "account_id": self.accounts["700000"].id,
                        "price_unit": 20,
                        "quantity": 2,
                    },
                )
            ],
        }
        inv_be = self.env["account.move"].with_company(self.company).create(data)
        inv_be.action_post()

        # Customer Invoice for Portuguese customer
        data = {
            "company_id": self.company.id,
            "partner_id": self.portugal_customer.id,
            "move_type": "out_invoice",
            "journal_id": self.journal_sale.id,
            "invoice_date": "2024-01-01",
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": "Test PT Tax",
                        "account_id": self.accounts["700000"].id,
                        "price_unit": 30,
                        "quantity": 3,
                    },
                )
            ],
        }
        inv_pt = self.env["account.move"].with_company(self.company).create(data)
        inv_pt.action_post()

        vat_book = self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book",
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": "2024",
                "period_type": "1T",
                "date_start": "2024-01-01",
                "date_end": "2024-03-31",
            }
        )
        vat_book.button_calculate()

        # Test Issued Tax Summary
        self.assertTrue(len(vat_book.issued_tax_summary_ids), 3)
        es_line = vat_book.issued_tax_summary_ids.filtered(
            lambda a: a.tax_id == inv_es.invoice_line_ids.mapped("tax_ids")
        )
        self.assertTrue(len(es_line), 1)
        self.assertEqual(es_line.base_amount, 10)
        self.assertNotEqual(es_line.tax_amount, 0)

        be_line = vat_book.issued_tax_summary_ids.filtered(
            lambda a: a.tax_id == inv_be.invoice_line_ids.mapped("tax_ids")
        )
        self.assertTrue(len(be_line), 1)
        self.assertEqual(be_line.base_amount, 40)
        self.assertEqual(be_line.tax_amount, 0)

        pt_line = vat_book.issued_tax_summary_ids.filtered(
            lambda a: a.tax_id == inv_pt.invoice_line_ids.mapped("tax_ids")
        )
        self.assertTrue(len(pt_line), 1)
        self.assertEqual(pt_line.base_amount, 90)
        self.assertEqual(pt_line.tax_amount, 0)
