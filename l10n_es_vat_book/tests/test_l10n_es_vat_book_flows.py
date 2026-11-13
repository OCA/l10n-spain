# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from typing import ClassVar

from odoo.exceptions import UserError
from odoo.fields import Command

from .test_l10n_es_aeat_vat_book import TestL10nEsAeatVatBookBase


class TestL10nEsVatBookFlows(TestL10nEsAeatVatBookBase):
    taxes_sale: ClassVar[dict] = {"S_IVA21S": (100, 21)}
    taxes_purchase: ClassVar[dict] = {"P_IVA21_SC": (200, 42)}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Company data are set by an administrator
        cls.company.sudo().vat = "ES12345678Z"
        cls.customer.vat = "ES12345678Z"
        cls.supplier.vat = "ES87654321X"

    def _create_vat_book(self, **vals):
        return self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2017,
                "period_type": "1T",
                "date_start": "2017-01-01",
                "date_end": "2017-03-31",
                **vals,
            }
        )

    def test_map_lines_match_company_taxes(self):
        """Every tax of the book map exists in a company with the Odoo core chart."""
        for map_line in self.env["aeat.vat.book.map.line"].search([]):
            xmlids = map_line.tax_xmlid_ids.mapped("name")
            taxes = map_line.get_taxes_for_company(self.company)
            self.assertEqual(len(taxes), len(xmlids), map_line.name)

    def test_ignored_taxes_out_of_book(self):
        sale_taxes = self._get_taxes("S_IVA0_NS") | self._get_taxes("OSS_S_IVA_NS")
        for tax in sale_taxes:
            self._invoice_sale_create(
                "2017-01-10",
                extra_vals={
                    "invoice_line_ids": [
                        Command.create(
                            {
                                "name": "Not subject",
                                "account_id": self.accounts["700000"].id,
                                "price_unit": 100,
                                "tax_ids": [Command.set(tax.ids)],
                            }
                        )
                    ]
                },
            )
        self._invoice_purchase_create(
            "2017-01-10",
            extra_vals={
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Exempt import",
                            "account_id": self.accounts["600000"].id,
                            "price_unit": 100,
                            "tax_ids": [
                                Command.set(self._get_taxes("P_DUA_EXEMPT").ids)
                            ],
                        }
                    )
                ]
            },
        )
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        self.assertFalse(vat_book.line_ids)
        self.assertFalse(vat_book.issued_tax_summary_ids)
        self.assertFalse(vat_book.received_tax_summary_ids)

    def test_exceptions_block_confirmation(self):
        self.supplier.vat = False
        anonymous = self.customer.copy(
            {"vat": False, "aeat_anonymous_cash_customer": True}
        )
        self._invoice_sale_create("2017-01-10", extra_vals={"partner_id": anonymous.id})
        self._invoice_purchase_create("2017-01-11")
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        self.assertFalse(vat_book.issued_line_ids.exception_text)
        self.assertEqual(
            vat_book.received_line_ids.exception_text, self.env._("Without VAT")
        )
        self.assertEqual(vat_book.error_count, 1)
        with self.assertRaises(UserError):
            vat_book.button_confirm()
        # Once the supplier has its VAT number the book can be confirmed
        self.supplier.vat = "ES87654321X"
        vat_book.button_calculate()
        self.assertEqual(vat_book.error_count, 0)
        vat_book.button_confirm()
        self.assertEqual(vat_book.state, "done")

    def test_auto_renumber(self):
        bill_2 = self._invoice_purchase_create("2017-02-01")
        bill_1 = self._invoice_purchase_create("2017-01-15")
        refund = self._invoice_refund(bill_2, "2017-02-10")
        vat_book = self._create_vat_book(auto_renumber=True)
        vat_book.button_calculate()
        lines = vat_book.received_line_ids.sorted("entry_number")
        self.assertEqual(lines.mapped("entry_number"), [1, 2])
        self.assertEqual(lines.move_id, bill_1 | bill_2)
        self.assertEqual(lines[0].move_id, bill_1)
        self.assertEqual(vat_book.rectification_received_line_ids.move_id, refund)
        self.assertEqual(vat_book.rectification_received_line_ids.entry_number, 1)

    def test_view_buttons(self):
        vat_book = self._create_vat_book()
        vat_book.button_calculate()
        action = vat_book.view_issued_invoices()
        self.assertEqual(
            action["report_name"],
            "l10n_es_vat_book.report_vat_book_invoices_issued_html",
        )
        action = vat_book.view_received_invoices()
        self.assertEqual(
            action["report_name"],
            "l10n_es_vat_book.report_vat_book_invoices_received_html",
        )

    def test_other_company_user(self):
        vat_book = self._create_vat_book()
        other_company = self.env["res.company"].sudo().create({"name": "Other company"})
        other_user = (
            self.env["res.users"]
            .sudo()
            .with_context(no_reset_password=True)
            .create(
                {
                    "name": "Other company AEAT user",
                    "login": "other_company_aeat_user",
                    "company_id": other_company.id,
                    "company_ids": [Command.set(other_company.ids)],
                    "group_ids": [
                        Command.set(
                            [
                                self.env.ref("account.group_account_manager").id,
                                self.env.ref("l10n_es_aeat.group_account_aeat").id,
                            ]
                        )
                    ],
                }
            )
        )
        books = self.env["l10n.es.vat.book"].with_user(other_user).search([])
        self.assertNotIn(vat_book, books)
