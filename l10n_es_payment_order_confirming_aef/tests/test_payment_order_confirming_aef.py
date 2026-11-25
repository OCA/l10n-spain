# Copyright 2023 Tecnativa - Ernesto García Medina
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import timedelta

from odoo import Command, fields
from odoo.exceptions import UserError
from odoo.tests import Form, tagged

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

    def _set_company_bank(self):
        company_bank = self.env["res.partner.bank"].create(
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
        self.bank_journal.write({"bank_account_id": company_bank.id})

    def _set_supplier(self, country, vat, bank_vals):
        self.partner.write(
            {
                "vat": vat,
                "street": " Calle Leonardo da Vinci, 7",
                "city": "Madrid",
                "zip": "41092",
                "country_id": country.id,
                "bank_ids": [Command.create(bank_vals)],
            }
        )
        self.invoice.partner_bank_id = self.partner.bank_ids[-1].id

    def test_account_payment_order_aef_success(self):
        self.set_payment_mode_aef()
        self._set_company_bank()
        self._set_supplier(
            self.env.ref("base.es"),
            "40538337D",
            {
                "account_number": "FR20 1242 1242 1242 1242 1242 124",
                "bank_name": "La Banque Postale",
                "bank_bic": "PSSTFRPPXXX",
            },
        )
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

    def test_account_payment_order_aef_ascii(self):
        """Names and addresses are exported in ASCII, so a letter that
        Windows-1252 does not have doesn't break the file"""
        self.set_payment_mode_aef()
        self._set_company_bank()
        self._set_supplier(
            self.env.ref("base.es"),
            "40538337D",
            {
                "account_number": "FR20 1242 1242 1242 1242 1242 124",
                "bank_name": "La Banque Postale",
                "bank_bic": "PSSTFRPPXXX",
            },
        )
        self.partner.write(
            {"name": "Antonín Dvořák, S.L.", "street": "Plaza de España, 1"}
        )
        order = self.order_creation(False)
        lines = self._payment_file_lines(order)
        self.assertEqual(lines[2][1:71].strip(), "Antonin Dvorak, S.L.")
        self.assertEqual(lines[2][91:156].strip(), "Plaza de Espana, 1")
        self.assertEqual(len(lines[2]), len(lines[0]))

    def test_account_payment_order_aef_international(self):
        self.set_payment_mode_aef()
        self._set_company_bank()
        self._set_supplier(
            self.env.ref("base.us"),
            "123456789",
            {"account_number": "0123-4567 89", "bank_bic": "CHASUS33XXX"},
        )
        order = self.order_creation(False)
        lines = self._payment_file_lines(order)
        # Account without IBAN in the field of international payments
        self.assertEqual(lines[4][2:36].strip(), "")
        self.assertEqual(lines[4][36:47], "CHASUS33XXX")
        self.assertEqual(lines[4][47:81].strip(), "0123456789")
        self.assertEqual(lines[4][81:83], "US")

    def test_account_payment_order_aef_sepa_without_iban(self):
        self.set_payment_mode_aef()
        self._set_company_bank()
        self._set_supplier(
            self.env.ref("base.es"),
            "40538337D",
            {"account_number": "0123 4567 89", "bank_bic": "CAIXESBBXXX"},
        )
        with self.assertRaisesRegex(UserError, "no es un IBAN"):
            self.order_creation(False)

    def test_payment_method_only_in_bank_journals(self):
        method = self.env.ref(
            "l10n_es_payment_order_confirming_aef.export_confirming_aef"
        )
        for journal_type in ("bank", "cash", "credit"):
            with Form(self.env["account.journal"]) as journal_form:
                journal_form.name = f"New {journal_type} journal"
                journal_form.type = journal_type
                # Methods that can be added to the journal
                available = journal_form.available_payment_method_ids
            if journal_type == "bank":
                self.assertIn(method, available)
            else:
                self.assertNotIn(method, available)
