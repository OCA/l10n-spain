# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestInvoiceAddress(TransactionCase):

    def setUp(self):
        super(TestInvoiceAddress, self).setUp()
        self.currency = self.env.ref("base.EUR")
        self.company = self.env.ref("base.main_company")
        vals = {
            "company_id": self.company.id,
            "type": "sale",
            "code": "TEST",
            "name": "Journal Test",
        }
        self.journal = self.env["account.journal"].create(vals)
        vals = {
            "name": "Customer",
            "customer": True,
            "supplier": False,
        }
        self.partner = self.env["res.partner"].create(vals)
        self.account = self.env["account.account"].search(
            [
                (
                    "user_type_id",
                    "=",
                    self.env.ref("account.data_account_type_receivable").id,
                )
            ],
            limit=1,
        )
        tbai_tax_map_id = self.env["tbai.tax.map"].search([("code", "=", "BNS")]).id
        vals = {
            "name": "Tax 22%",
            "amount": 22,
            "price_include": False,
            "not_subject_to_cause": "IE",
            "tbai_tax_map_id": tbai_tax_map_id
        }
        self.tax = self.env["account.tax"].create(vals)

    def test_no_subject_invoice(self):
        vals = {
            "currency_id": self.currency.id,
            "partner_id": self.partner.id,
            "reference_type": "none",
            "journal_id": self.journal.id,
            "account_id": self.account.id,
        }
        invoice = self.env["account.invoice"].create(vals)
        vals = {
            "name": "Product 001",
            "quantity": 1,
            "price_unit": 100,
            "invoice_line_tax_ids": [(6, 0, [self.tax.id])],
            "invoice_id": invoice.id,
            "account_id": self.account.id,
        }
        self.env["account.invoice.line"].create(vals)
        invoice._onchange_invoice_line_ids()
        self.assertEqual(len(invoice.invoice_line_ids), 1)
        is_subject_tax = (
            invoice.invoice_line_ids[0].invoice_line_tax_ids.tbai_is_subject_to_tax())
        self.assertFalse(is_subject_tax)
        invoice.compute_taxes()
        self.assertEqual(len(invoice.tax_line_ids), 1)
        self.assertTrue(invoice.tax_line_ids.tbai_es_entrega())
        self.assertFalse(invoice.tax_line_ids.tbai_es_prestacion_servicios())
        self.assertEqual(invoice.tax_line_ids.tbai_get_value_causa(), "IE")
