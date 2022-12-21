# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2012-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from datetime import date, timedelta

from odoo.exceptions import ValidationError

from odoo.addons.account_payment_order.tests.test_payment_order_inbound import (
    TestPaymentOrderInboundBase,
)


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
        account_account_risk_1 = self.env.ref("l10n_es.1_account_common_4311")
        account_account_risk_2 = self.env.ref("l10n_es.1_account_common_5208")
        payment_order = self.inbound_order
        self.assertEqual(len(payment_order.ids), 1)
        bank_journal = self.env["account.journal"].search(
            [("type", "=", "bank")], limit=1
        )
        # Set journal to allow cancelling entries
        bank_journal.update_posted = True
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
                "cancel_risk": False,
                "discounted_commercial_effects_id": account_account_risk_1.id,
                "debit_discounted_effects_id": account_account_risk_2.id,
                "show_bank_account": "full",
            }
        )

        payment_order.write(
            {"journal_id": bank_journal.id, "payment_mode_id": payment_mode}
        )

        self.assertEqual(len(payment_order.payment_line_ids), 1)
        self.assertEqual(len(payment_order.bank_line_ids), 0)

        # Open payment order
        payment_order.draft2open()

        self.assertEqual(payment_order.bank_line_count, 1)

        # Generate and upload
        payment_order.open2generated()
        payment_order.risk_accounting_date = date.today()
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
                "control_risk": False,
                "cancel_risk": True,
                "discounted_commercial_effects_id": account_account_risk_1.id,
                "debit_discounted_effects_id": account_account_risk_2.id,
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
        ).filtered(lambda x: x.account_id.id == account_account_risk_1.id)
        self.create_payment_lines(inbound_order_cancel, move_line_to_create_payments)
        inbound_order_cancel.payment_line_ids[
            0
        ].amount_currency = move_line_to_create_payments[0].debit
        inbound_order_cancel.draft2open()

        inbound_order_cancel.open2generated()
        inbound_order_cancel.generated2uploaded()

        payment_mode.write({"cancel_risk": True, "control_risk": False})
        payment_mode.write({"cancel_risk": False, "control_risk": True})

    def create_payment_lines(self, payment_order, move_line_ids):
        if move_line_ids:
            move_line_ids.create_payment_line_from_move_line(payment_order)
        return True
