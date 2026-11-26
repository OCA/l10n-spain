# Copyright 2026 César Andrés Sánchez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import TestVerifactuCommon


@tagged("post_install", "-at_install")
class TestVerifactuSealedEntry(TestVerifactuCommon):
    """Business-rule protection for sealed VERI*FACTU invoice entries.

    Distinguishes:
    - ACL denial (Accounting users)
    - Business-rule denial (Settings vs sealed RF)
    - Relational integrity (FK while response lines exist — covered elsewhere)
    """

    def _settings_user(self):
        return self.env["res.users"].create(
            {
                "name": "VERI*FACTU Settings",
                "login": f"verifactu_settings_{self.env.cr.dbname}",
                "groups_id": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("base.group_system").id,
                        ]
                    )
                ],
            }
        )

    def _invoice_user(self):
        return self.env["res.users"].create(
            {
                "name": "VERI*FACTU Invoice",
                "login": f"verifactu_invoice_{self.env.cr.dbname}",
                "groups_id": [
                    Command.set(
                        [
                            self.env.ref("base.group_user").id,
                            self.env.ref("account.group_account_invoice").id,
                        ]
                    )
                ],
            }
        )

    def _prepare_sealed_not_sent(self):
        self._activate_certificate(self.certificate_password)
        invoice = self._create_and_prepare_invoice(date="2026-06-01", amount=88)
        invoice._generate_verifactu_chaining()
        entry = invoice.last_verifactu_invoice_entry_id
        self.assertTrue(entry)
        self.assertTrue(entry.document_hash)
        self.assertTrue(entry.aeat_json_data)
        self.assertEqual(entry.send_state, "not_sent")
        self.assertFalse(entry.response_line_ids)
        return invoice, entry

    def _attach_sent_response(self, entry):
        response = (
            self.env["verifactu.invoice.entry.response"]
            .sudo()
            .create(
                {
                    "header": "{}",
                    "name": "Synthetic AEAT response",
                    "invoice_data": "[]",
                    "response": {},
                    "verifactu_csv": "CSV-TEST",
                }
            )
        )
        line = (
            self.env["verifactu.invoice.entry.response.line"]
            .sudo()
            .create(
                {
                    "entry_id": entry.id,
                    "entry_response_id": response.id,
                    "model": entry.model,
                    "document_id": entry.document_id,
                    "send_state": "sent",
                }
            )
        )
        entry.last_response_line_id = line
        entry.invalidate_recordset(["send_state", "response_line_ids"])
        self.assertEqual(entry.send_state, "sent")
        return response, line

    def test_settings_cannot_unlink_sealed_not_sent(self):
        """CASO A: sealed not_sent entry blocked by business rule (Settings)."""
        _invoice, entry = self._prepare_sealed_not_sent()
        admin = self._settings_user()
        entry_id = entry.id
        with self.assertRaises(UserError):
            entry.with_user(admin).unlink()
        self.assertTrue(
            self.env["verifactu.invoice.entry"].browse(entry_id).exists(),
            "Sealed not_sent entry must remain after Settings unlink attempt",
        )

    def test_settings_cannot_unlink_sealed_sent_after_response_lines(self):
        """CASO B+C: sealed sent entry stays after response-line removal attempt."""
        _invoice, entry = self._prepare_sealed_not_sent()
        _response, line = self._attach_sent_response(entry)
        admin = self._settings_user()
        entry_id = entry.id
        line_id = line.id

        with self.assertRaises(UserError):
            line.with_user(admin).unlink()
        self.assertTrue(
            self.env["verifactu.invoice.entry.response.line"].browse(line_id).exists(),
            "Response line of a sealed entry must not be deleted by Settings",
        )

        # Even if M2O pointers are cleared, the sealed entry itself stays protected
        entry.write({"last_response_line_id": False})
        with self.assertRaises(UserError):
            entry.with_user(admin).unlink()
        self.assertTrue(self.env["verifactu.invoice.entry"].browse(entry_id).exists())

    def test_unsealed_entry_can_be_unlinked(self):
        """CASO D: non-sealed (empty hash) entries remain deletable."""
        self._activate_certificate(self.certificate_password)
        invoice = self._create_and_prepare_invoice(date="2026-06-02", amount=10)
        entry = self.env["verifactu.invoice.entry"].create(
            {
                "document_id": invoice.id,
                "model": invoice._name,
                "company_id": self.company.id,
                "verifactu_chaining_id": self.company.verifactu_chaining_id.id,
                "document_hash": "",
            }
        )
        entry_id = entry.id
        entry.unlink()
        self.assertFalse(self.env["verifactu.invoice.entry"].browse(entry_id).exists())

    def test_accounting_user_denied_by_acl(self):
        """CASO E: Accounting denial is ACL AccessError, not the business rule."""
        _invoice, entry = self._prepare_sealed_not_sent()
        user = self._invoice_user()
        with self.assertRaises(AccessError):
            entry.with_user(user).unlink()

    def test_force_unlink_context_allows_cleanup(self):
        """Test/demo cleanup may delete sealed rows with an explicit context flag."""
        _invoice, entry = self._prepare_sealed_not_sent()
        entry_id = entry.id
        entry.with_context(verifactu_force_unlink=True).unlink()
        self.assertFalse(self.env["verifactu.invoice.entry"].browse(entry_id).exists())
