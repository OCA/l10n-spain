# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import UserError, ValidationError

from .common import TestVerifactuCommon


class TestVerifactuJournal(TestVerifactuCommon):
    def test_sale_journal_requires_verifactu(self):
        with self.assertRaises(ValidationError):
            self.env["account.journal"].create(
                {
                    "name": "Strict VERI*FACTU journal",
                    "code": "SVF",
                    "type": "sale",
                    "company_id": self.company.id,
                    "verifactu_enabled": False,
                }
            )

        with self.assertRaises(ValidationError):
            self.journal.write({"verifactu_enabled": False})

    def test_legacy_journal_cannot_post_customer_invoice(self):
        journal = self.env["account.journal"].create(
            {
                "name": "Legacy non-VERI*FACTU journal",
                "code": "LVF",
                "type": "sale",
                "company_id": self.company.id,
            }
        )
        self.env.cr.execute(
            "UPDATE account_journal SET verifactu_enabled = FALSE WHERE id = %s",
            [journal.id],
        )
        journal.invalidate_recordset(["verifactu_enabled"])
        invoice = self.invoice.copy({"journal_id": journal.id})

        with self.assertRaises(UserError):
            invoice.action_post()
        self.assertEqual(invoice.state, "draft")

    def test_other_companies_and_move_types_are_unchanged(self):
        company = self.env["res.company"].create({"name": "Non-VERI*FACTU company"})
        journal = self.env["account.journal"].create(
            {
                "name": "Non-VERI*FACTU company journal",
                "code": "NVC",
                "type": "sale",
                "company_id": company.id,
                "verifactu_enabled": False,
            }
        )
        self.assertFalse(journal.verifactu_enabled)

        purchase_journal = self.env["account.journal"].create(
            {
                "name": "Non-VERI*FACTU purchase journal",
                "code": "NVP",
                "type": "purchase",
                "company_id": self.company.id,
                "verifactu_enabled": False,
            }
        )
        bill = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": purchase_journal.id,
                "partner_id": self.partner.id,
                "invoice_date": "2026-01-01",
                "move_type": "in_invoice",
                "invoice_line_ids": [
                    Command.create(
                        {
                            "product_id": self.product.id,
                            "account_id": self.account_expense.id,
                            "name": "Purchase line",
                            "price_unit": 100,
                            "quantity": 1,
                        }
                    )
                ],
            }
        )
        bill.action_post()
        self.assertEqual(bill.state, "posted")

        general_journal = self.env["account.journal"].create(
            {
                "name": "Non-VERI*FACTU general journal",
                "code": "NVG",
                "type": "general",
                "company_id": self.company.id,
                "verifactu_enabled": False,
            }
        )
        income_account = self.env.ref(f"l10n_es.{self.company.id}_account_common_7000")
        entry = self.env["account.move"].create(
            {
                "company_id": self.company.id,
                "journal_id": general_journal.id,
                "move_type": "entry",
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self.account_expense.id,
                            "name": "Debit line",
                            "debit": 100,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": income_account.id,
                            "name": "Credit line",
                            "credit": 100,
                        }
                    ),
                ],
            }
        )
        entry.action_post()
        self.assertEqual(entry.state, "posted")
