# Copyright 2022 Tecnativa - Pedro M. Baeza
# Copyright 2022 Tecnativa - Víctor Martínez
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0
import logging
import re

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

    def _export_369(self):
        wizard = self.env["l10n.es.aeat.report.export_to_boe"].create({})
        # The fixture report is dated 2017, so the 2022+ config is passed explicitly
        export_config = self.env.ref(
            "l10n_es_aeat_mod369.aeat_mod369_2022_main_export_config"
        )
        content = wizard._export_config(self.model369, export_config)
        return content.decode("iso-8859-1")

    @staticmethod
    def _get_export_pages(content):
        return [
            match.group(0)
            for match in re.finditer(r"<T369(\d\d)>.*?</T369\1>", content, flags=re.S)
        ]

    @staticmethod
    def _page_items(page, tag, item_size):
        body = page[len("<%s>" % tag) + 1 : -len("</%s>" % tag)]
        return [body[i : i + item_size] for i in range(0, 28 * item_size, item_size)]

    def _create_goods_lines(self, total):
        """Complete spain_goods_line_ids with positive base lines up to ``total``."""
        goods = self.model369.spain_goods_line_ids.filtered(lambda x: x.base > 0)
        self.assertGreaterEqual(len(goods), 1, "Expected goods lines in the fixture")
        sources = list(goods)
        index = len(sources)
        while len(self.model369.spain_goods_line_ids.filtered(lambda x: x.base > 0)) < (
            total
        ):
            source = sources[index % len(sources)]
            self.env["l10n.es.aeat.mod369.line.grouped"].create(
                {
                    "report_id": self.model369.id,
                    "country_id": self.env.ref("base.es").id,
                    "oss_country_id": source.oss_country_id.id,
                    "tax_id": source.tax_id.id,
                    "mod369_line_ids": [(6, 0, source.mod369_line_ids.ids)],
                }
            )
            index += 1
        self.model369.invalidate_cache()
        goods = self.model369.spain_goods_line_ids.filtered(lambda x: x.base > 0)
        self.assertEqual(len(goods), total)

    def test_model_369_export_file_baseline(self):
        self.model369.button_calculate()
        pages = self._get_export_pages(self._export_369())
        self.assertEqual(
            [page[:8] for page in pages],
            [
                "<T36900>",
                "<T36904>",
                "<T36905>",
                "<T36906>",
                "<T36907>",
                "<T36908>",
                "<T36909>",
            ],
        )
        self.assertEqual(
            [len(page) for page in pages], [110, 1423, 1211, 1687, 1687, 763, 5803]
        )
        items = (
            "FR02000 0000000000001000000000000000002000"
            "FR01000 0000000000001000000000000000001000"
            "FR00550 0000000000001000000000000000000550"
            "DE01900 0000000000001000000000000000001900"
            "DE00700 0000000000001000000000000000000700"
        )
        self.assertEqual(pages[2], "<T36905> " + items + " " * 983 + "</T36905>")
        self.assertEqual(pages[5], "<T36908> " + " " * 745 + "</T36908>")

    def test_model_369_export_goods_complementary_pages(self):
        self.model369.button_calculate()
        self._create_goods_lines(57)
        pages = [
            page
            for page in self._get_export_pages(self._export_369())
            if page.startswith("<T36905>")
        ]
        self.assertEqual(len(pages), 3, "Expected 3 goods pages for 57 lines")
        self.assertEqual([page[8] for page in pages], [" ", "C", "C"])
        self.assertEqual(len({len(page) for page in pages}), 1)
        self.assertEqual(len(set(pages)), 3, "Each page must use its own lines")
        counts = [
            len([item for item in self._page_items(page, "T36905", 42) if item.strip()])
            for page in pages
        ]
        self.assertEqual(counts, [28, 28, 1])
        self.assertEqual(sum(counts), 57)

    def test_model_369_export_goods_single_page_at_limit(self):
        self.model369.button_calculate()
        self._create_goods_lines(28)
        source = self.model369.spain_goods_line_ids.filtered(lambda x: x.base > 0)[0]
        self.env["l10n.es.aeat.mod369.line.grouped"].create(
            {
                "report_id": self.model369.id,
                "country_id": self.env.ref("base.es").id,
                "oss_country_id": source.oss_country_id.id,
                "tax_id": source.tax_id.id,
            }
        )
        self.model369.invalidate_cache()
        self.assertEqual(len(self.model369.spain_goods_line_ids), 29)
        pages = [
            page
            for page in self._get_export_pages(self._export_369())
            if page.startswith("<T36905>")
        ]
        self.assertEqual(len(pages), 1, "28 lines with base > 0 fit in one page")
        self.assertEqual(pages[0][8], " ")
        items = self._page_items(pages[0], "T36905", 42)
        self.assertEqual(len([item for item in items if item.strip()]), 28)

    def test_model_369_export_corrections_complementary_pages(self):
        self.model369.button_calculate()
        grouped_model = self.env["l10n.es.aeat.mod369.line.grouped"]
        for index in range(29):
            grouped_model.create(
                {
                    "report_id": self.model369.id,
                    "country_id": self.env.ref("base.es").id,
                    "oss_country_id": self.oss_countries["FR"].id,
                    "is_refund": True,
                    "refund_fiscal_year": 2016,
                    "refund_period": "T%d" % (index % 4 + 1),
                    "tax_correction": -(index + 1) - 0.37,
                }
            )
        self.model369.invalidate_cache()
        self.assertEqual(len(self.model369.refund_line_ids), 29)
        pages = [
            page
            for page in self._get_export_pages(self._export_369())
            if page.startswith("<T36908>")
        ]
        self.assertEqual(len(pages), 2, "Expected 2 corrections pages for 29 lines")
        self.assertEqual([page[8] for page in pages], [" ", "C"])
        self.assertEqual(len({len(page) for page in pages}), 1)
        counts = [
            len([item for item in self._page_items(page, "T36908", 26) if item.strip()])
            for page in pages
        ]
        self.assertEqual(counts, [28, 1])
        self.assertIn("-0000000000000137", self._page_items(pages[0], "T36908", 26)[0])
        self.assertIn("-0000000000002937", self._page_items(pages[1], "T36908", 26)[0])

    def test_model_369_amount_strings_rounded_and_signed(self):
        grouped_model = self.env["l10n.es.aeat.mod369.line.grouped"]
        self.assertEqual(
            grouped_model._format_export_amount(16720.469999999998),
            "00000000001672047",
        )
        self.assertEqual(
            grouped_model._format_export_amount(-15.37), "-0000000000001537"
        )
        self.assertEqual(
            grouped_model._format_export_amount(-16720.469999999998),
            "-0000000001672047",
        )
        line = grouped_model.create(
            {
                "report_id": self.model369.id,
                "is_refund": True,
                "tax_correction": -18.8,
            }
        )
        self.assertEqual(line.tax_correction_str, "-0000000000001880")

    def test_model_369_account_move_zero_amount(self):
        self.model369.button_calculate()
        self.model369.total_amount = 0
        with self.assertRaises(UserError):
            self.create_account_move()
