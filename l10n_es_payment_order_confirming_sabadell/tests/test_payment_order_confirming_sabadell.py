# Copyright 2021 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields
from odoo.tests import Form, common


class TestPaymentOrderConfirmingSabadell(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.a_expense = cls.env["account.account"].create(
            {
                "code": "TEA",
                "name": "Test Expense Account",
                "account_type": "expense",
            }
        )
        cls.bank_journal = cls.env["account.journal"].create(
            {
                "name": "Test bank",
                "type": "bank",
                "code": "test-bank",
                "bank_account_id": cls.env.ref(
                    "account_payment_mode.main_company_iban"
                ).id,
            }
        )
        cls.bank_journal.bank_account_id.acc_holder_name = "acc_holder_name"
        cls.bank_journal.bank_account_id.partner_id.vat = "ES40538337D"
        cls.purchase_journal = cls.env["account.journal"].create(
            {"name": "Test purchase", "type": "purchase", "code": "test2-purchase"}
        )
        cls.payment_mode = cls.env["account.payment.mode"].create(
            {
                "name": "Sabadell confirming",
                "payment_method_id": cls.env.ref(
                    "l10n_es_payment_order_confirming_sabadell.confirming_sabadell"
                ).id,
                "bank_account_link": "fixed",
                "fixed_journal_id": cls.bank_journal.id,
                "contrato_bsconfirming": "TEST-CODE",
                "conf_sabadell_type": "58",
            }
        )
        cls.partner = cls.env["res.partner"].create(
            {
                "name": "Mr Odoo",
                "email": "demo@demo.com",
                "vat": "40538337D",
                "street": " Calle Leonardo da Vinci, 7",
                "city": "Madrid",
                "zip": "41092",
                "phone": "976123456",
                "country_id": cls.env.ref("base.es").id,
                "state_id": cls.env.ref("base.state_es_m").id,
            }
        )
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.invoice = cls._create_invoice(cls)
        cls.env.ref("account_payment_mode.main_company_iban2").partner_id = cls.partner

    def _create_invoice(self):
        move_form = Form(
            self.env["account.move"].with_context(
                default_move_type="in_invoice",
                default_journal_id=self.purchase_journal.id,
            )
        )
        move_form.partner_id = self.partner
        move_form.ref = "custom_ref"
        move_form.invoice_date = fields.date.today()
        move_form.payment_mode_id = self.payment_mode
        with move_form.invoice_line_ids.new() as line_form:
            line_form.product_id = self.product
            line_form.quantity = 1.0
            line_form.price_unit = 100.00
        move = move_form.save()
        move.action_post()
        return move

    def _create_payment_order(self):
        payment_order = self.env["account.payment.order"].create(
            {"payment_mode_id": self.payment_mode.id}
        )
        line_create = (
            self.env["account.payment.line.create"]
            .with_context(
                active_model="account.payment.order", active_id=payment_order.id
            )
            .create({"date_type": "move", "move_date": fields.date.today()})
        )
        line_create.journal_ids = self.purchase_journal.ids
        line_create.move_line_filters_change()
        line_create.populate()
        line_create.create_payment_lines()
        return payment_order

    def test_account_payment_order_sabadell(self):
        payment_order = self._create_payment_order()
        payment_order.draft2open()
        payment_order.open2generated()
        self.assertEqual(payment_order.state, "generated")
