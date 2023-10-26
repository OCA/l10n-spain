# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.modules.module import get_module_resource
from odoo.tests import common


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
        n43_file_path = get_module_resource(
            "l10n_es_account_statement_import_n43", "tests", "test.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        cls.import_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )

    def test_import_n43_multi(self):
        n43_file_path = get_module_resource(
            "l10n_es_account_statement_import_n43", "tests", "testmulti.n43"
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
