# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import common
from odoo.tools.misc import file_path


class L10nEsAccountStatementImportN43(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create(
            {"name": "Test partner N43", "company_id": cls.env.company.id}
        )
        cls.partner_bank = cls.env["res.partner.bank"].create(
            {
                "acc_number": "000000000000000000000000",
                "company_id": cls.env.company.id,
                "partner_id": cls.env.company.partner_id.id,
            }
        )
        cls.partner_bank_01 = cls.env["res.partner.bank"].create(
            {
                "acc_number": "000000000000001000000000",
                "company_id": cls.env.company.id,
                "partner_id": cls.env.company.partner_id.id,
            }
        )
        eur_currency = cls.env.ref("base.EUR")
        eur_currency.write({"active": True})
        cls.journal = cls.env["account.journal"].create(
            {
                "type": "bank",
                "name": "Test N43 bank",
                "code": "BN43",
                "company_id": cls.env.company.id,
                "bank_account_id": cls.partner_bank.id,
                "currency_id": eur_currency.id,
            }
        )
        cls.journal_01 = cls.env["account.journal"].create(
            {
                "type": "bank",
                "name": "Test N43 bank",
                "code": "BN432",
                "company_id": cls.env.company.id,
                "bank_account_id": cls.partner_bank_01.id,
                "currency_id": eur_currency.id,
            }
        )
        n43_file_path = file_path("l10n_es_account_statement_import_n43/tests/test.n43")
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        cls.import_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )

    def test_import_n43_multi(self):
        n43_file_path = file_path(
            "l10n_es_account_statement_import_n43/tests/testmulti.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        self.import_wizard.statement_file = n43_file
        action = self.import_wizard.with_context(journal_id=False).import_file_button()
        self.assertTrue(action)
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal.id)]
        )
        self.assertEqual(1, len(statements))
        statements = self.env["account.bank.statement"].search(
            [("journal_id", "=", self.journal_01.id)]
        )
        self.assertEqual(1, len(statements))

    def test_import_n43(self):
        action = self.import_wizard.import_file_button()
        self.assertTrue(action)
        statement_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        statement = statement_lines[2].statement_id
        self.assertEqual(len(statement_lines), 3)
        self.assertTrue(
            statement_lines.filtered(lambda st: str(st.date) == "2016-05-25")
        )
        self.assertTrue(
            statement_lines.filtered(lambda st: str(st.date) == "2016-05-16")
        )
        self.assertTrue(
            statement_lines.filtered(lambda st: str(st.date) == "2016-05-12")
        )
        self.assertEqual(statement_lines[0].date, fields.Date.to_date("2016-05-25"))
        self.assertAlmostEqual(statement.balance_start, 0, 2)
        self.assertAlmostEqual(statement.balance_end, 101.96, 2)
        self.assertEqual(statement_lines[2].partner_id, self.partner)
        self.assertEqual(statement_lines[2].ref, "000975737917")
        self.assertEqual(statement_lines[1].ref, "/")
        self.assertEqual(statement_lines[0].ref, "5540014210128010")

    def test_import_n43_fecha_oper(self):
        self.journal.n43_date_type = "fecha_oper"
        action = self.import_wizard.import_file_button()
        self.assertTrue(action)
        statements = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(statements[0].date, fields.Date.to_date("2016-05-26"))

    def test_import_n43_duplicate_file(self):
        """Importing the same N43 file twice should not create duplicate lines.
        The second import must raise an error because all transactions already
        exist, and no new lines should be created."""
        self.import_wizard.import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 3)
        # Re-import same file: all lines are duplicates, must raise
        n43_file_path = file_path("l10n_es_account_statement_import_n43/tests/test.n43")
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        wizard2 = (
            self.env["account.statement.import"]
            .with_context(journal_id=self.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )
        with self.assertRaises(UserError):
            wizard2.import_file_button()
        # Still 3 lines, not 6
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 3)

    def test_import_n43_duplicate_overlap(self):
        """Importing a second file that overlaps with the first one should only
        create the new lines. The overlapping file (test_overlap.n43) contains
        the same 3 movements as test.n43 plus 1 extra movement. Only the new
        movement should be imported; the 3 duplicates must be skipped."""
        self.import_wizard.import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 3)
        # Import overlapping file: 3 duplicates + 1 new
        n43_file_path = file_path(
            "l10n_es_account_statement_import_n43/tests/test_overlap.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        wizard2 = (
            self.env["account.statement.import"]
            .with_context(journal_id=self.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test overlap"})
        )
        wizard2.import_file_button()
        # 3 original + 1 new = 4
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 4)

    def test_import_n43_same_lines(self):
        """Two identical transactions on the same day (e.g. two bank fees of
        the same amount) must both be imported, because they have different
        sequence numbers in the file."""
        n43_file_path = file_path(
            "l10n_es_account_statement_import_n43/tests/test_same_lines.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        wizard = (
            self.env["account.statement.import"]
            .with_context(journal_id=self.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test same"})
        )
        wizard.import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        # Both identical lines must be imported
        self.assertEqual(len(st_lines), 2)

    def test_import_n43_excluded_patern(self):
        self.journal.n43_exclude_pattern = r".*TEST PARTNER 2.*"
        self.import_wizard.import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 2)
