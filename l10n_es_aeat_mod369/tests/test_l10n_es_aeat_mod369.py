# Copyright 2022 Tecnativa - Pedro M. Baeza
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
import logging

from odoo.exceptions import UserError

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
        cls.company.country_id = cls.env.ref("base.es").id
        cls.company.account_fiscal_country_id = cls.env.ref("base.es").id
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
        for country_code in self.sale_invoices.keys():
            sale_invoice_by_key = self.sale_invoices[country_code]
            spain_goods_line_filter = self.model369.spain_goods_line_ids.filtered(
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

    def create_account_move(self):
        self.model369.journal_id = self.journal_misc.id
        account_template = self.env.ref("l10n_es.account_common_477")
        account_477 = self.model369.company_id.get_account_from_template(
            account_template
        )
        self.model369.counterpart_account_id = account_477.id
        self.model369.button_confirm()
        self.model369.button_post()

    def test_model_369_account_move_positive_amount(self):
        self.model369.button_calculate()
        self.create_account_move()
        self.assertEqual(self.model369.name, self.model369.move_id.ref)
        self.assertEqual(self.model369.move_id.journal_id, self.model369.journal_id)
        account_4750 = self.env["account.account"].search(
            [
                ("company_id", "=", self.model369.company_id.id),
                ("code", "=ilike", "4750%"),
            ]
        )
        debit_line = self.model369.move_id.line_ids[1]
        credit_line = self.model369.move_id.line_ids[0]
        self.assertEqual(
            self.model369.counterpart_account_id.id, debit_line.account_id.id
        )
        self.assertEqual(debit_line.debit, self.model369.total_amount)
        self.assertEqual(account_4750.id, credit_line.account_id.id)
        self.assertEqual(credit_line.credit, self.model369.total_amount)

    def test_model_369_account_move_negative_amount(self):
        self.model369.button_calculate()
        self.model369.total_amount *= -1
        self.create_account_move()
        self.assertEqual(self.model369.name, self.model369.move_id.ref)
        self.assertEqual(self.model369.move_id.journal_id, self.model369.journal_id)
        account_4700 = self.env["account.account"].search(
            [
                ("company_id", "=", self.model369.company_id.id),
                ("code", "=ilike", "4700%"),
            ]
        )
        debit_line = self.model369.move_id.line_ids[0]
        credit_line = self.model369.move_id.line_ids[1]
        self.assertEqual(
            self.model369.counterpart_account_id.id, credit_line.account_id.id
        )
        self.assertEqual(credit_line.credit, abs(self.model369.total_amount))
        self.assertEqual(account_4700.id, debit_line.account_id.id)
        self.assertEqual(debit_line.debit, abs(self.model369.total_amount))

    def test_model_369_account_move_zero_amount(self):
        self.model369.button_calculate()
        self.model369.total_amount = 0
        with self.assertRaises(UserError):
            self.create_account_move()
