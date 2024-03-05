# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import datetime, timedelta

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.account_payment_order.tests.test_payment_order_outbound import (
    TestPaymentOrderOutboundBase,
)


@tagged("post_install", "-at_install")
class TestPaymentOrderOutboundBaseAEF(TestPaymentOrderOutboundBase):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        super().setUpClass(chart_template_ref="l10n_es.account_chart_template_pymes")

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
                {"date_type": "move", "move_date": datetime.now() + timedelta(days=1)}
            )
        )
        line_create.payment_mode = "any"
        line_create.move_line_filters_change()
        line_create.populate()
        line_create.create_payment_lines()
        order.draft2open()
        order.open2generated()
        order.generated2uploaded()

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
                "acc_number": "FR76 4242 4242 4242 4242 4242 424",
                "bank_id": self.env.ref(
                    "account_payment_mode.bank_la_banque_postale"
                ).id,
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
                            "acc_number": "FR20 1242 1242 1242 1242 1242 124",
                            "bank_id": self.env.ref(
                                "account_payment_mode.bank_societe_generale"
                            ).id,
                        },
                    )
                ],
            }
        )
        self.invoice.partner_bank_id = self.partner.bank_ids[-1].id
        self.order_creation(False)
