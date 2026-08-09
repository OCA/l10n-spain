# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError, ValidationError
from odoo.tests.common import Form

from odoo.addons.l10n_es_verifactu_oca.tests.common import TestVerifactuCommon


class TestExternalVerifactuInvoice(TestVerifactuCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.external_journal = cls.env["account.journal"].create(
            {
                "name": "External SIF journal",
                "code": "EXT",
                "type": "sale",
                "company_id": cls.company.id,
                "verifactu_import_journal": True,
            }
        )

    def _create_external_invoice(self, journal=None):
        return self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": (journal or self.external_journal).id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "account_id": self.account_expense.id,
                            "name": "External SIF line",
                            "price_unit": 100,
                            "quantity": 1,
                        }
                    )
                ],
            }
        )

    def test_external_invoice_posts_without_verifactu_data(self):
        invoice = self._create_external_invoice()
        previous_entry = (
            self.company.verifactu_chaining_id.last_verifactu_invoice_entry_id
        )

        self.assertFalse(self.external_journal.verifactu_enabled)
        self.assertTrue(invoice.is_external_invoice)
        self.assertFalse(invoice.external_sif_id)
        self.assertFalse(invoice.external_sif_installation)
        self.assertFalse(invoice.external_rf_identifier)

        invoice.action_post()

        self.assertEqual(invoice.state, "posted")
        self.assertTrue(invoice.line_ids)
        self.assertFalse(invoice.verifactu_enabled)
        self.assertFalse(invoice.last_verifactu_invoice_entry_id)
        self.assertFalse(invoice.verifactu_hash)
        self.assertFalse(invoice.verifactu_hash_string)
        self.assertFalse(invoice.verifactu_qr)
        self.assertEqual(
            self.company.verifactu_chaining_id.last_verifactu_invoice_entry_id,
            previous_entry,
        )

    def test_external_invoice_can_be_paid_and_reconciled(self):
        invoice = self._create_external_invoice()
        invoice.action_post()
        payment_form = Form(
            self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=invoice.ids
            )
        )
        payment_form.journal_id = self.journal_cash
        payment_form.payment_date = invoice.invoice_date

        payment_form.save().action_create_payments()

        self.assertEqual(invoice.payment_state, "paid")

    def test_external_invoice_cannot_be_printed_or_sent(self):
        invoice = self._create_external_invoice()
        invoice.action_post()
        for method in (
            invoice.action_invoice_print,
            invoice.action_invoice_sent,
            invoice.action_send_and_print,
            invoice.preview_invoice,
        ):
            with self.assertRaises(UserError):
                method()
        with self.assertRaises(UserError):
            self.env["ir.actions.report"]._render_qweb_pdf(
                "account.account_invoices", res_ids=invoice.ids
            )

    def test_external_journal_is_immutable(self):
        with self.assertRaises(ValidationError):
            self.env["account.journal"].create(
                {
                    "name": "Invalid external SIF journal",
                    "code": "EXG",
                    "type": "general",
                    "company_id": self.company.id,
                    "verifactu_import_journal": True,
                }
            )
        with self.assertRaises(ValidationError):
            self.external_journal.write({"verifactu_import_journal": False})
        with self.assertRaises(ValidationError):
            self.external_journal.write({"type": "general"})

        self.invoice.action_post()
        with self.assertRaises(ValidationError):
            self.invoice.journal_id.write({"verifactu_import_journal": True})

    def test_external_journal_can_be_created_from_form(self):
        journal_form = Form(
            self.env["account.journal"].with_context(default_company_id=self.company.id)
        )
        journal_form.name = "External SIF journal from form"
        journal_form.code = "EXF"
        journal_form.type = "sale"
        journal_form.verifactu_import_journal = True

        journal = journal_form.save()

        self.assertTrue(journal.verifactu_import_journal)
        self.assertFalse(journal.verifactu_enabled)

    def test_legacy_non_verifactu_journal_can_be_adopted(self):
        legacy_journal = self.env["account.journal"].create(
            {
                "name": "Legacy external SIF journal",
                "code": "LEX",
                "type": "sale",
                "company_id": self.company.id,
            }
        )
        self.company.write({"verifactu_enabled": False})
        legacy_journal.write({"verifactu_enabled": False})
        historical_invoice = self._create_external_invoice(journal=legacy_journal)
        historical_invoice.action_post()
        self.company.write({"verifactu_enabled": True})
        self.assertTrue(legacy_journal.verifactu_enabled)

        legacy_journal.write({"verifactu_import_journal": True})

        self.assertTrue(legacy_journal.verifactu_import_journal)
        self.assertFalse(legacy_journal.verifactu_enabled)
        self.assertEqual(historical_invoice.state, "posted")
        self.assertTrue(historical_invoice.is_external_invoice)

    def test_company_activation_keeps_external_journal_disabled(self):
        self.company.write({"verifactu_enabled": True})
        self.assertFalse(self.external_journal.verifactu_enabled)

    def test_normal_invoice_keeps_verifactu_flow(self):
        self.invoice.action_post()
        self.assertTrue(self.invoice.verifactu_enabled)
        self.assertTrue(self.invoice.last_verifactu_invoice_entry_id)
