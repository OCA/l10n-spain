# Copyright 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import SavepointCase


class TestRefundAccount(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestRefundAccount, cls).setUpClass()
        Account = cls.env["account.account"]
        cls.user_type = cls.env["account.account.type"].create({
            "name": "Test User Type",
        })
        cls.dummy_account = Account.create({
            "name": "Dummy Account",
            "code": "700",
            "user_type_id": cls.user_type.id,
        })
        cls.refund_in_account = Account.create({
            "name": "Account Refund In",
            "code": "608",
            "user_type_id": cls.user_type.id,
        })
        cls.refund_out_account = Account.create({
            "name": "Account Refund Out",
            "code": "708",
            "user_type_id": cls.user_type.id,
        })
        cls.product_category = cls.env["product.category"].create({
            "name": "Test Category",
            "property_account_refund_in_categ_id": cls.refund_in_account.id,
            "property_account_refund_out_categ_id": cls.refund_out_account.id,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "property_account_refund_in_id": cls.refund_in_account.id,
            "property_account_refund_out_id": cls.refund_out_account.id,
            "categ_id": cls.product_category.id,
        })
        cls.partner = cls.env["res.partner"].create({
            "name": "Test Partner",
        })

    def test_direct_invoice(self):
        """Test account is propagated when a direct invoice is created"""
        Invoice = self.env["account.invoice"]
        invoice_in = Invoice.create({
            "partner_id": self.partner.id,
            "type": "in_refund",
            "invoice_line_ids": [(0, 0, {
                "quantity": 1.0,
                "name": "Great Product",
                "price_unit": 10.0,
                "account_id": self.dummy_account.id,
            })]
        })
        invoice_line = invoice_in.mapped("invoice_line_ids")
        invoice_line.product_id = self.product.id
        invoice_line._onchange_product_id()
        self.assertEqual(
            invoice_line.account_id.code, self.refund_in_account.code)
        self.product.property_account_refund_in_id = False
        self.product.property_account_refund_out_id = False
        invoice_out = Invoice.create({
            "partner_id": self.partner.id,
            "type": "out_refund",
            "invoice_line_ids": [(0, 0, {
                "quantity": 1.0,
                "name": "Great Product",
                "price_unit": 10.0,
                "account_id": self.dummy_account.id,
            })]
        })
        invoice_line = invoice_out.mapped("invoice_line_ids")
        invoice_line.product_id = self.product.id
        invoice_line._onchange_product_id()
        self.assertEqual(
            invoice_line.account_id.code, self.refund_out_account.code)

    def test_refund_invoice(self):
        """Test account is propagated when a refund invoice is created"""
        Invoice = self.env["account.invoice"]
        invoice_in = Invoice.create({
            "partner_id": self.partner.id,
            "type": "in_invoice",
            "invoice_line_ids": [(0, 0, {
                "quantity": 1.0,
                "name": "Great Product",
                "price_unit": 10.0,
                "account_id": self.dummy_account.id,
                "product_id": self.product.id,
            })]
        })
        refund_invoice = invoice_in.refund()
        invoice_line = refund_invoice.mapped("invoice_line_ids")
        invoice_line._onchange_product_id()
        self.assertEqual(
            invoice_line.account_id.code, self.refund_in_account.code)
        self.product.property_account_refund_in_id = False
        self.product.property_account_refund_out_id = False
        invoice_out = Invoice.create({
            "partner_id": self.partner.id,
            "type": "out_invoice",
            "invoice_line_ids": [(0, 0, {
                "quantity": 1.0,
                "name": "Great Product",
                "price_unit": 10.0,
                "account_id": self.dummy_account.id,
                "product_id": self.product.id,
            })]
        })
        refund_invoice = invoice_out.refund()
        invoice_line = refund_invoice.mapped("invoice_line_ids")
        invoice_line._onchange_product_id()
        self.assertEqual(
            invoice_line.account_id.code, self.refund_out_account.code)
