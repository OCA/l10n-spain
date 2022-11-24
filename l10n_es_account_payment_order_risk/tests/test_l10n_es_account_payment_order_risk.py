# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2012-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date, timedelta

from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form, SavepointCase
from odoo.addons.account_payment_order.tests.test_payment_order_inbound import (
    TestPaymentOrderInboundBase,
)


class TestL10nEsAccountPaymentOrderRisk(SavepointCase):
    @classmethod
    def setUpClass(cls):
        self = cls
        super().setUpClass()
        self.env.user.company_id = self.env.ref("base.main_company").id
        self.invoice_line_account = self.env["account.account"].create(
            {
                "name": "Test account",
                "code": "TEST1",
                "user_type_id": self.env.ref("account.data_account_type_revenue").id,
            }
        )
        self.account_account_risk_1 = self.env.ref("l10n_es.1_account_common_4311")
        self.account_account_risk_2 = self.env.ref("l10n_es.1_account_common_5208")
        self.journal = self.env["account.journal"].create(
            {"name": "Test journal", "code": "BANK", "type": "bank"}
        )
        payment_mode = self.env["account.payment.mode"].create(
            {
                "name": "CONTROL RISK",
                "active": True,
                "payment_type": "inbound",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "payment_order_ok": True,
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "default_payment_mode": "same",
                "default_target_move": "all",
                "default_date_type": "due",
                "generate_move": True,
                "offsetting_account": "bank_account",
                "move_option": "line",
                "post_move": True,
                "control_risk": True,
                "discounted_commercial_effects_id": self.account_account_risk_1.id,
                "debit_discounted_effects_id": self.account_account_risk_2.id,
                "show_bank_account": "full",
            }
        )
        self.inbound_mode = payment_mode
        self.inbound_mode.variable_journal_ids = self.journal
        # Make sure no others orders are present
        self.domain = [
            ("state", "=", "draft"),
            ("payment_type", "=", "inbound"),
            ("company_id", "=", self.env.user.company_id.id),
        ]
        self.payment_order_obj = self.env["account.payment.order"]
        self.payment_order_obj.search(self.domain).unlink()
        # Create payment order
        self.inbound_order = self.env["account.payment.order"].create(
            {
                "payment_type": "inbound",
                "payment_mode_id": self.inbound_mode.id,
                "journal_id": self.journal.id,
                "risk_accounting_date": date.today(),
            }
        )
        # Open invoice
        self.invoice = self._create_customer_invoice(self)
        self.invoice.action_post()
        # Add to payment order using the wizard
        self.env["account.invoice.payment.line.multi"].with_context(
            active_model="account.move", active_ids=self.invoice.ids
        ).create({}).run()

    def _create_customer_invoice(self):
        with Form(
            self.env["account.move"].with_context(default_type="out_invoice")
        ) as invoice_form:
            invoice_form.partner_id = self.env.ref("base.res_partner_4")
            with invoice_form.invoice_line_ids.new() as invoice_line_form:
                invoice_line_form.product_id = self.env.ref("product.product_product_4")
                invoice_line_form.name = "product that cost 100"
                invoice_line_form.quantity = 1
                invoice_line_form.price_unit = 100.0
                invoice_line_form.account_id = self.invoice_line_account
                invoice_line_form.tax_ids.clear()
        invoice = invoice_form.save()
        invoice_form = Form(invoice)
        invoice_form.payment_mode_id = self.inbound_mode
        return invoice_form.save()


class TestPaymentOrderInbound(TestPaymentOrderInboundBase):
    def test_constrains_type(self):
        with self.assertRaises(ValidationError):
            order = self.env["account.payment.order"].create(
                {"payment_mode_id": self.inbound_mode.id, "journal_id": self.journal.id}
            )
            order.payment_type = "outbound"

    def test_constrains_date(self):
        with self.assertRaises(ValidationError):
            self.inbound_order.date_scheduled = date.today() - timedelta(days=1)

    def test_creation(self):
        payment_order = self.inbound_order
        self.assertEqual(len(payment_order.ids), 1)
        bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        # Set journal to allow cancelling entries
        bank_journal.update_posted = True

        payment_order.write({"journal_id": bank_journal.id})

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        # Open payment order
        payment_order.draft2open()

        self.assertEqual(payment_order.bank_line_count, 1)

        # Generate and upload
        payment_order.open2generated()
        payment_order.generated2uploaded()

        payment_mode_cancel = self.env["account.payment.mode"].create(
            {
                "name": "CANCEL RISK",
                "active": True,
                "payment_type": "inbound",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in"
                ).id,
                "payment_order_ok": True,
                "bank_account_link": "fixed",
                "fixed_journal_id": self.journal.id,
                "default_payment_mode": "same",
                "default_target_move": "all",
                "default_date_type": "due",
                "generate_move": True,
                "offsetting_account": "bank_account",
                "move_option": "line",
                "post_move": True,
                "cancel_risk": True,
                "discounted_commercial_effects_id": self.account_account_risk_1.id,
                "debit_discounted_effects_id": self.account_account_risk_2.id,
                "show_bank_account": "full",
            }
        )

        # Create payment order
        inbound_order_cancel = self.env["account.payment.order"].create(
            {
                "payment_type": "inbound",
                "payment_mode_id": payment_mode_cancel.id,
                "journal_id": self.journal.id,
                "risk_accounting_date": date.today(),
            }
        )
        move_line_to_create_payments = payment_order.move_ids.mapped(
            "line_ids"
        ).filtered(lambda x: x.account_id.id == self.account_account_risk_1.id)
        self.create_payment_lines(inbound_order_cancel, move_line_to_create_payments)
        inbound_order_cancel.payment_line_ids[
            0
        ].amount_currency = move_line_to_create_payments[0].debit
        inbound_order_cancel.draft2open()

        inbound_order_cancel.open2generated()
        inbound_order_cancel.generated2uploaded()

        self.assertEqual(payment_order.state, "uploaded")
        with self.assertRaises(UserError):
            payment_order.unlink()

        bank_line = payment_order.bank_line_ids

        with self.assertRaises(UserError):
            bank_line.unlink()
        payment_order.action_done_cancel()
        self.assertEqual(payment_order.state, "cancel")
        payment_order.cancel2draft()
        payment_order.unlink()
        self.assertEqual(len(self.payment_order_obj.search(self.domain)), 0)
