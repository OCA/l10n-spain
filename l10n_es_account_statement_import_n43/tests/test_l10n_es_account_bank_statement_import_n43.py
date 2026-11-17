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
                "account_number": "000000000000000000000000",
                "company_id": cls.env.company.id,
                "partner_id": cls.env.company.partner_id.id,
            }
        )
        cls.partner_bank_01 = cls.env["res.partner.bank"].create(
            {
                "account_number": "000000000000001000000000",
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
        with open(n43_file_path, "rb") as f:
            n43_file = base64.b64encode(f.read()).decode()
        cls.import_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )

    def test_import_n43_multi(self):
        n43_file_path = file_path(
            "l10n_es_account_statement_import_n43/tests/testmulti.n43"
        )
        with open(n43_file_path, "rb") as f:
            n43_file = base64.b64encode(f.read()).decode()
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

    def test_import_n43_excluded_patern(self):
        self.journal.n43_exclude_pattern = r".*TEST PARTNER 2.*"
        self.import_wizard.import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 2)

    def test_n43_partner_search_all_deterministic_order(self):
        """With n43_partner_search="all", heuristics are applied following
        the field selection order (caixabank, santander, sabadell)."""
        partner_st = self.env["res.partner"].create({"name": "Santander Match N43"})
        self.env["res.partner"].create({"name": "Sabadell Match N43"})
        line = {"conceptos": {"01": ("Santander Match N43", "Sabadell Match N43")}}
        partner = self.import_wizard._get_n43_partner(line, self.journal)
        self.assertEqual(partner, partner_st)

    def test_import_n43_own_company_not_matched(self):
        """A concept containing the company name must not set the own
        company as partner of the imported line."""
        self.env.company.partner_id.name = "Own Company N43 Test"
        n43_file_path = file_path("l10n_es_account_statement_import_n43/tests/test.n43")
        with open(n43_file_path, "rb") as f:
            n43_content = f.read().replace(b"TEST PARTNER N43", b"OWN COMPANY N43 TEST")
        self.import_wizard.statement_file = base64.b64encode(n43_content).decode()
        self.import_wizard.import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(len(st_lines), 3)
        matched_line = st_lines.filtered(lambda line: line.ref == "000975737917")
        self.assertFalse(matched_line.partner_id)

    def test_import_n43_twice(self):
        """Importing the same file again doesn't duplicate the lines."""
        self.import_wizard.import_file_button()
        domain = [("statement_id.journal_id", "=", self.journal.id)]
        st_lines = self.env["account.bank.statement.line"].search(domain)
        self.assertEqual(len(st_lines), 3)
        self.assertTrue(all(st_lines.mapped("unique_import_id")))
        with self.assertRaisesRegex(UserError, "already imported"):
            self.import_wizard.import_file_button()
        self.assertEqual(
            self.env["account.bank.statement.line"].search(domain), st_lines
        )

    def test_import_n43_final_balance_with_zero_initial_balance(self):
        """The final balance is checked even if the initial one is zero."""
        n43_file_path = file_path("l10n_es_account_statement_import_n43/tests/test.n43")
        with open(n43_file_path, "rb") as f:
            n43_content = f.read().replace(b"00000010196978", b"00000020196978")
        self.import_wizard.statement_file = base64.b64encode(n43_content).decode()
        with self.assertRaisesRegex(UserError, "Final balance amount"):
            self.import_wizard.import_file_button()

    def test_import_not_n43(self):
        """A file that is not N43 falls to the next importer in the chain."""
        content = b"11/05/2026;PAYMENT 101;100,00\n12/05/2026;PAYMENT 102;50,50\n"
        self.import_wizard.statement_file = base64.b64encode(content).decode()
        with self.assertRaisesRegex(UserError, "format is not supported"):
            self.import_wizard.import_file_button()

    def test_n43_partner_search_own_company_does_not_hide_real_partner(self):
        """The own company is left out of the search, so it can't hide a real
        partner that matches the same text."""
        self.env.company.partner_id.name = "Own Company N43 Test"
        real_partner = self.env["res.partner"].create(
            {"name": "Own Company N43 Test SL"}
        )
        self.journal.n43_partner_search = "santander"
        line = {"conceptos": {"01": ("Own Company N43 Test", "")}}
        partner = self.import_wizard._get_n43_partner(line, self.journal)
        self.assertEqual(partner, real_partner)

    def test_import_n43_journal_matched_by_bank_and_branch(self):
        """Accounts of different banks can share the 10 digits of the account
        number, so the bank and branch codes are used to choose the journal."""
        partner_bank = self.env["res.partner.bank"].create(
            {
                "account_number": "ES00123456780000000000",
                "company_id": self.env.company.id,
                "partner_id": self.env.company.partner_id.id,
            }
        )
        journal = self.journal.copy(
            {"name": "Other bank", "code": "BN43B", "bank_account_id": partner_bank.id}
        )
        n43_file_path = file_path("l10n_es_account_statement_import_n43/tests/test.n43")
        with open(n43_file_path, "rb") as f:
            n43_content = f.read().replace(b"1100000000", b"1112345678", 1)
        self.import_wizard.statement_file = base64.b64encode(n43_content).decode()
        # Without journal in the context, to match it from the file contents
        self.import_wizard.with_context(journal_id=False).import_file_button()
        st_lines = self.env["account.bank.statement.line"].search(
            [("journal_id", "in", (self.journal + journal).ids)]
        )
        self.assertEqual(st_lines.journal_id, journal)
