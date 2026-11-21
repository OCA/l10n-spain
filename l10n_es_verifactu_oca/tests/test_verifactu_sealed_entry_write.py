# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import TestVerifactuCommon


@tagged("post_install", "-at_install")
class TestVerifactuSealedEntryWrite(TestVerifactuCommon):
    """Once its hash is generated, the data of a VERI*FACTU entry is frozen."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.invoice_user = cls.env["res.users"].create(
            {
                "name": "VERI*FACTU invoicing user",
                "login": "verifactu_sealed_write_user",
                "groups_id": [
                    Command.set(
                        [
                            cls.env.ref("base.group_user").id,
                            cls.env.ref("account.group_account_invoice").id,
                        ]
                    )
                ],
            }
        )

    def _create_sealed_entry(self):
        self._activate_certificate(self.certificate_password)
        invoice = self._create_and_prepare_invoice(date="2026-06-01", amount=88)
        invoice._generate_verifactu_chaining()
        entry = invoice.last_verifactu_invoice_entry_id
        self.assertTrue(entry.document_hash)
        self.assertTrue(entry.aeat_json_data)
        return entry

    def test_chaining_seals_hash_and_json_together(self):
        """Generating the chaining stores both values despite the protection."""
        entry = self._create_sealed_entry()
        self.assertEqual(len(entry.document_hash), 64)

    def test_cannot_change_hash_of_sealed_entry(self):
        entry = self._create_sealed_entry()
        original_hash = entry.document_hash
        with self.assertRaises(UserError):
            entry.with_user(self.invoice_user).write({"document_hash": "TAMPERED"})
        self.assertEqual(entry.document_hash, original_hash)

    def test_cannot_change_aeat_data_of_sealed_entry(self):
        entry = self._create_sealed_entry()
        with self.assertRaises(UserError):
            entry.with_user(self.invoice_user).write({"aeat_json_data": "{}"})

    def test_cannot_change_sealed_data_even_as_superuser(self):
        entry = self._create_sealed_entry()
        with self.assertRaises(UserError):
            entry.sudo().write({"previous_invoice_entry_id": False, "model": "x"})

    def test_same_value_and_other_fields_still_writable(self):
        """Rewriting the same value, or non-sealed fields, is still allowed."""
        entry = self._create_sealed_entry()
        entry.with_user(self.invoice_user).write(
            {"document_hash": entry.document_hash, "send_attempt": 3}
        )
        self.assertEqual(entry.send_attempt, 3)

    def test_unsealed_entry_is_writable(self):
        entry = self.env["verifactu.invoice.entry"].create(
            {
                "verifactu_chaining_id": self.verifactu_chaining.id,
                "model": "account.move",
                "document_id": 0,
                "company_id": self.company.id,
                "document_hash": "",
            }
        )
        entry.write({"document_hash": "ABC", "aeat_json_data": "{}"})
        self.assertEqual(entry.document_hash, "ABC")
