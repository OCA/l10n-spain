# Copyright 2025 Process Control - Jorge Luis López
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import ValidationError

from .common import TestVerifactuCommon


class TestAccountJournal(TestVerifactuCommon):
    def test_journal_hash_modification_validation(self):
        """Test validation when disabling hash restriction on VERI*FACTU enabled journals"""
        # Create a sale journal with VERI*FACTU enabled
        journal = self.env["account.journal"].create(
            {
                "name": "Test Sale Journal",
                "type": "sale",
                "code": "TSJ",
                "company_id": self.company.id,
                "verifactu_enabled": True,
                "restrict_mode_hash_table": True,
            }
        )

        # Test that we cannot disable hash restriction on VERI*FACTU enabled sale journal
        with self.assertRaises(ValidationError) as cm:
            journal.write({"restrict_mode_hash_table": False})
        self.assertIn("restricted hash modification", str(cm.exception))

        # Test that creation fails with invalid combination
        with self.assertRaises(ValidationError) as cm:
            self.env["account.journal"].create(
                {
                    "name": "Invalid Journal",
                    "type": "sale",
                    "code": "INV",
                    "company_id": self.company.id,
                    "verifactu_enabled": True,
                    "restrict_mode_hash_table": False,
                }
            )
        self.assertIn("restricted hash modification", str(cm.exception))

    def test_journal_non_sale_type_allowed(self):
        """Test that non-sale journals can have hash restriction disabled"""
        # Purchase journal should work without restrictions
        journal = self.env["account.journal"].create(
            {
                "name": "Test Purchase Journal",
                "type": "purchase",
                "code": "TPJ",
                "company_id": self.company.id,
                "verifactu_enabled": True,
                "restrict_mode_hash_table": False,
            }
        )
        self.assertFalse(journal.restrict_mode_hash_table)

        # Should be able to modify it too
        journal.write({"restrict_mode_hash_table": True})
        self.assertTrue(journal.restrict_mode_hash_table)

    def test_journal_company_verifactu_disabled(self):
        """Test that journals work when company VERI*FACTU is disabled"""
        # Disable VERI*FACTU on company
        self.company.verifactu_enabled = False

        # Should be able to create sale journal without hash restriction
        journal = self.env["account.journal"].create(
            {
                "name": "Test Journal No Company VERI*FACTU",
                "type": "sale",
                "code": "TJN",
                "company_id": self.company.id,
                "verifactu_enabled": True,
                "restrict_mode_hash_table": False,
            }
        )
        self.assertFalse(journal.restrict_mode_hash_table)
