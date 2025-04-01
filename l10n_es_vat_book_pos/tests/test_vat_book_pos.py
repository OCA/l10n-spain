# Copyright 2025 APSL-Nagarro Antoni Marroig
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from datetime import datetime

from odoo.addons.l10n_es_vat_book.tests.test_l10n_es_aeat_vat_book import (
    TestL10nEsAeatVatBook,
)


class TestVATBookPOS(TestL10nEsAeatVatBook):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config = cls.env["pos.config"].search([("company_id", "=", cls.company.id)])
        cls.product_id = cls.env["product.product"].create(
            {"name": "Test POS", "available_in_pos": True, "list_price": 200}
        )

    def _create_session(self):
        self.config.open_ui()
        session = self.config.current_session_id
        session.set_cashbox_pos(0, None)
        return session

    def _create_order(self, session, product_id, amount):
        tax = self.env.ref(f"account.{self.company.id}_account_tax_template_s_iva21b")
        pos_order = self.env["pos.order"].create(
            {
                "company_id": self.company.id,
                "session_id": session.id,
                "lines": [
                    (
                        0,
                        0,
                        {
                            "name": "Test/0001",
                            "product_id": self.product_id.id,
                            "price_unit": amount,
                            "qty": 1.0,
                            "price_subtotal": amount,
                            "price_subtotal_incl": amount * 1.21,
                            "tax_ids": [[6, False, [tax.id]]],
                        },
                    )
                ],
                "amount_tax": amount * 0.21,
                "amount_total": amount * 1.21,
                "amount_paid": 0,
                "amount_return": 0,
                "last_order_preparation_change": "{}",
            }
        )
        context_make_payment = {
            "active_ids": [pos_order.id],
            "active_id": pos_order.id,
            "company_id": self.company.id,
        }
        pos_make_payment = (
            self.env["pos.make.payment"]
            .with_context(**context_make_payment)
            .create({"amount": amount * 1.21})
        )
        context_payment = {"active_id": pos_order.id}
        pos_make_payment.with_context(**context_payment).check()

    def test_vat_book_pos(self):
        session = self._create_session()
        self._create_order(session, self.product_id, 2)
        session.action_pos_session_closing_control()
        self.company.vat = "ESA12345674"
        vat_book = self.env["l10n.es.vat.book"].create(
            {
                "name": "Test VAT Book",
                "company_id": self.company.id,
                "company_vat": "A12345674",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": f"{datetime.now().year}",
                "period_type": "0A",
                "date_start": f"{datetime.now().year}-01-01",
                "date_end": f"{datetime.now().year}-12-31",
            }
        )
        vat_book.button_calculate()
        self.assertEqual(
            len(vat_book.issued_line_ids.filtered(lambda x: "POS" in x.ref)), 1
        )
        self.assertEqual(vat_book.error_count, 0)
