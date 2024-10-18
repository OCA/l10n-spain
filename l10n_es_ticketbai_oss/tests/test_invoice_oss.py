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
        }
        self.partner = self.env["res.partner"].create(vals)

        self.account = self.env["account.account"].create(
            {
                "name": "Receivables Account",
                "code": "REC",
                "company_id": self.company.id,
                "account_type": "asset_receivable",
            }
        )

        tbai_tax_map_id = self.env["tbai.tax.map"].search([("code", "=", "BNS")]).id
        vals = {
            "name": "Tax 22%",
            "amount": 22,
            "price_include": False,
            "not_subject_to_cause": "IE",
            "tbai_tax_map_id": tbai_tax_map_id,
        }
        self.tax = self.env["account.tax"].create(vals)

    def test_no_subject_invoice(self):
        vals = {
            "currency_id": self.currency.id,
            "partner_id": self.partner.id,
            "journal_id": self.journal.id,
            "ref": "INV/12345",
        }
        invoice = self.env["account.move"].create(vals)

        vals = {
            "name": "Product 001",
            "quantity": 1,
            "price_unit": 100,
            "tax_ids": [(6, 0, [self.tax.id])],
            "move_id": invoice.id,
            "account_id": self.account.id,
        }
        self.env["account.move.line"].create(vals)

        self.assertEqual(len(invoice.invoice_line_ids), 1)

        is_subject_tax = invoice.invoice_line_ids[0].tax_ids.tbai_is_subject_to_tax()
        self.assertFalse(is_subject_tax)

        self.assertEqual(len(invoice.line_ids.tax_ids), 1)
        self.assertFalse(invoice.line_ids.tax_ids.tbai_es_entrega())
        self.assertFalse(invoice.line_ids.tax_ids.tbai_es_prestacion_servicios())
        self.assertEqual(invoice.line_ids.tax_ids.tbai_get_value_causa(invoice), "IE")
