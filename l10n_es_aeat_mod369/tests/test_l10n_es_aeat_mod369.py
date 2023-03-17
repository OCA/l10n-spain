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

    def setUp(self):
        super().setUp()
        general_tax = self.env.ref(
            "l10n_es.%s_account_tax_template_s_iva21b" % self.company.id
        )
        self.oss_taxes = {}
        self.oss_countries = {}
        self.sale_invoices = {}
        invoice_date = "2017-01-01"
        for country_key in ["FR", "DE"]:
            country = self.env.ref("base.%s" % country_key.lower())
            wizard = self.env["l10n.eu.oss.wizard"].create(
                {
                    "company_id": self.company.id,
                    "general_tax": general_tax.id,
                    "todo_country_ids": [(4, country.id)],
                }
            )
            wizard.generate_eu_oss_taxes()
            tax = self.env["account.tax"].search(
                [
                    ("oss_country_id", "=", country.id),
                    ("company_id", "=", self.company.id),
                ]
            )
            tax.service_type = "goods"
            line_data = {
                "name": "Test for OSS tax",
                "account_id": self.accounts["700000"].id,
                "price_unit": 100,
                "quantity": 1,
                "invoice_line_tax_ids": [(4, tax.id)],
            }
            extra_vals = {"invoice_line_ids": [(0, 0, line_data)]}
            invoice = self._invoice_sale_create(invoice_date, extra_vals)
            self.sale_invoices[country_key] = invoice
            self.oss_taxes[country_key] = tax
            self.oss_countries[country_key] = country
        # 369
        model369_model = self.env["l10n.es.aeat.mod369.report"].sudo(
            self.account_manager
        )
        self.model369 = model369_model.create(
            {
                "company_id": self.company.id,
                "company_vat": "1234567890",
                "contact_name": "Test owner",
                "type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
            }
        )

    def test_model_369(self):
        self.model369.button_calculate()
        total_sale_invoices_tax = 0
        self.assertFalse(self.model369.spain_services_line_ids)
        self.assertFalse(self.model369.spain_goods_line_ids)
        for country_code in self.sale_invoices.keys():
            sale_invoice_by_key = self.sale_invoices[country_code]
            spain_goods_line_filter = self.model369.goods_line_ids.filtered(
                lambda x, country_code=country_code: x.country_code == country_code
                and not x.is_page_8_line
            )
            self.assertEqual(
                self.oss_taxes[country_code].amount, spain_goods_line_filter.vat_type
            )
            self.assertEqual(
                spain_goods_line_filter.amount, sale_invoice_by_key.amount_tax
            )
            total_sale_invoices_tax += sale_invoice_by_key.amount_tax
            self.assertEqual(
                spain_goods_line_filter.base, sale_invoice_by_key.amount_untaxed
            )
        self.assertEqual(self.model369.total_amount, total_sale_invoices_tax)
