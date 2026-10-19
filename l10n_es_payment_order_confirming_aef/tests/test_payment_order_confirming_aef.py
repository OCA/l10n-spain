# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account_payment_order.tests.test_payment_order_outbound import (
    TestPaymentOrderOutboundBase,
)


@tagged("post_install", "-at_install")
class TestPaymentOrderOutboundBaseAEF(TestPaymentOrderOutboundBase):
    def order_creation(self, date_prefered):
        # Open invoice
        self.invoice.action_post()
        order_vals = {
            "payment_type": "outbound",
            "payment_mode_id": self.creation_mode.id,
        }
        if date_prefered:
            order_vals["date_prefered"] = date_prefered
        order = self.env["account.payment.order"].create(order_vals)
        order.payment_mode_id = self.mode.id
        order.payment_mode_id_change()
        line_create = (
            self.env["account.payment.line.create"]
            .with_context(active_model="account.payment.order", active_id=order.id)
            .create(
                {
                    "date_type": "move",
                    "filter_date": fields.Datetime.now() + timedelta(days=1),
                }
            )
        )
        line_create.payment_mode = "any"
        line_create._compute_move_line_domain()
        line_create.populate()
        line_create.create_payment_lines()
        order.draft2open()
        order.open2generated()
        order.generated2uploaded()
        return order

    def _payment_file_lines(self, order):
        attachment = self.env["ir.attachment"].search(
            [("res_model", "=", "account.payment.order"), ("res_id", "=", order.id)]
        )
        return attachment.raw.decode("Windows-1252").split("\r\n")

    def set_payment_mode_aef(self):
        self.mode.write(
            {
                "group_lines": False,
                "bank_account_link": "fixed",
                "default_date_prefered": "due",
                "fixed_journal_id": self.bank_journal.id,
                "payment_method_id": self.env.ref(
                    "l10n_es_payment_order_confirming_aef.export_confirming_aef"
                ).id,
                "aef_confirming_type": "T",
            }
        )
        self.mode.variable_journal_ids = self.bank_journal

    def test_account_payment_order_aef_errors(self):
        self.set_payment_mode_aef()
        with self.assertRaises(UserError):
            self.order_creation(False)

    def test_account_payment_order_aef_success(self):
        self.set_payment_mode_aef()
        bank_journal = self.env["res.partner.bank"].create(
            {
                "account_number": "FR76 4242 4242 4242 4242 4242 424",
                "bank_name": "La Banque Postale",
                "bank_bic": "PSSTFRPPXXX",
                "partner_id": self.company.partner_id.id,
            }
        )
        self.company.partner_id.write(
            {
                "vat": "40538337D",
                "country_id": self.env.ref("base.es").id,
                "state_id": self.env.ref("base.state_es_m").id,
            }
        )
        self.bank_journal.write({"bank_account_id": bank_journal.id})
        self.partner.write(
            {
                "vat": "40538337D",
                "street": " Calle Leonardo da Vinci, 7",
                "city": "Madrid",
                "zip": "41092",
                "country_id": self.env.ref("base.es").id,
                "state_id": self.env.ref("base.state_es_m").id,
                "bank_ids": [
                    (
                        0,
                        0,
                        {
                            "account_number": "FR20 1242 1242 1242 1242 1242 124",
                            "bank_name": "La Banque Postale",
                            "bank_bic": "PSSTFRPPXXX",
                        },
                    )
                ],
            }
        )
        self.invoice.partner_bank_id = self.partner.bank_ids[-1].id
        order = self.order_creation(False)
        lines = self._payment_file_lines(order)
        self.assertEqual([line[:1] for line in lines], list("1234567") + [""])
        # Charge account of the company
        self.assertEqual(lines[0][102:136].strip(), "FR7642424242424242424242424")
        # Transfer to the IBAN and BIC of the supplier
        self.assertEqual(lines[4][1], "T")
        self.assertEqual(lines[4][2:36].strip(), "FR2012421242124212421242124")
        self.assertEqual(lines[4][36:47], "PSSTFRPPXXX")
        self.assertEqual(lines[4][47:81].strip(), "")
