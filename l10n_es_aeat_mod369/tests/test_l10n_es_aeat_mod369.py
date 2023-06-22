# Copyright 2022 Tecnativa - Pedro M. Baeza
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
import logging

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)

_logger = logging.getLogger("aeat.369")


class TestL10nEsAeatMod369Base(TestL10nEsAeatModBase):
    # Set 'debug' attribute to True to easy debug this test
    # Do not forget to include '--log-handler aeat:DEBUG' in Odoo command line
    debug = False

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        general_tax = cls.env.ref(
            "l10n_es.%s_account_tax_template_s_iva21b" % cls.company.id
        )
        reduced_tax = cls.env.ref(
            "l10n_es.%s_account_tax_template_s_iva10b" % cls.company.id
        )
        superreduced_tax = cls.env.ref(
            "l10n_es.%s_account_tax_template_s_iva4b" % cls.company.id
        )
        cls.oss_taxes = {}
        cls.oss_countries = {}
        cls.sale_invoices = {}
        invoice_date = "2017-01-01"
        for country_key in ["FR", "DE"]:
            country = cls.env.ref("base.%s" % country_key.lower())
            wizard = cls.env["l10n.eu.oss.wizard"].create(
                {
                    "company_id": cls.company.id,
                    "general_tax": general_tax.id,
                    "reduced_tax": reduced_tax.id,
                    "superreduced_tax": superreduced_tax.id,
                    "todo_country_ids": [(4, country.id)],
                }
            )
            wizard.generate_eu_oss_taxes()
            taxes = cls.env["account.tax"].search(
                [
                    ("oss_country_id", "=", country.id),
                    ("company_id", "=", cls.company.id),
                ]
            )
            fpo = cls.env["account.fiscal.position"].search(
                [("country_id", "=", country.id), ("oss_oca", "=", True)], limit=1
            )
            # FR has 3 taxes, DE has 2
            tax_g = taxes[0]
            tax_r = taxes[1]
            if country_key == "FR":
                tax_sr = taxes[2]
                tax_g.service_type = "goods"
                lines_data = [
                    (
                        0,
                        0,
                        {
                            "name": "Test for OSS tax",
                            "account_id": cls.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_g.ids)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test for OSS tax - reduced",
                            "account_id": cls.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_r.ids)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test for OSS tax - superreduced",
                            "account_id": cls.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_sr.ids)],
                        },
                    ),
                ]
            else:
                lines_data = [
                    (
                        0,
                        0,
                        {
                            "name": "Test for OSS tax",
                            "account_id": cls.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_g.ids)],
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Test for OSS tax - reduced",
                            "account_id": cls.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [(6, 0, tax_r.ids)],
                        },
                    ),
                ]

            extra_vals = {"fiscal_position_id": fpo.id, "invoice_line_ids": lines_data}
            invoice = cls._invoice_sale_create(invoice_date, extra_vals)
            cls.sale_invoices[country_key] = invoice
            cls.oss_taxes[country_key] = taxes
            cls.oss_countries[country_key] = country
        # 369
        model369_model = cls.env["l10n.es.aeat.mod369.report"].with_user(
            cls.account_manager
        )
        cls.model369 = model369_model.create(
            {
                "company_id": cls.company.id,
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

    def test_model_369_amounts(self):
        self.model369.button_calculate()
        total_sale_invoices_tax = 0
        self.assertFalse(self.model369.spain_services_line_ids)
        self.assertFalse(self.model369.spain_goods_line_ids)
        for country_code in self.sale_invoices.keys():
            sale_invoice_by_key = self.sale_invoices[country_code]
            spain_goods_line_filter = self.model369.goods_line_ids.filtered(
                lambda x: x.country_code == country_code and not x.is_page_8_line
            )
            # checking type of tax
            country_amount_tax = sum(tax.amount for tax in self.oss_taxes[country_code])
            spain_goods_line_vat_type = sum(
                line.vat_type for line in spain_goods_line_filter
            )
            self.assertEqual(country_amount_tax, spain_goods_line_vat_type)
            # checking amount of tax
            spain_goods_line_amount = sum(
                line.amount for line in spain_goods_line_filter
            )
            self.assertEqual(spain_goods_line_amount, sale_invoice_by_key.amount_tax)
            # checking base of tax
            spain_goods_line_base = sum(line.base for line in spain_goods_line_filter)
            self.assertEqual(spain_goods_line_base, sale_invoice_by_key.amount_untaxed)

            total_sale_invoices_tax += sale_invoice_by_key.amount_tax
        self.assertEqual(self.model369.total_amount, total_sale_invoices_tax)

    def test_model_369_amounts_page_5_6(self):
        self.model369.button_calculate()
        total_sale_invoices_tax = 0
        for country_code in self.sale_invoices.keys():
            sale_invoice_by_key = self.sale_invoices[country_code]
            total_sale_invoices_tax += sale_invoice_by_key.amount_tax

        num_invoices_from_test = len(self.sale_invoices)
        num_invoices_from_mod369 = len(
            self.model369.tax_line_ids.mapped("move_line_ids").mapped("move_id")
        )
        self.assertEqual(num_invoices_from_test, num_invoices_from_mod369)
        pages_5_6_total = sum(self.model369.total_line_ids.mapped("page_5_6_total"))
        self.assertEqual(total_sale_invoices_tax, pages_5_6_total)
