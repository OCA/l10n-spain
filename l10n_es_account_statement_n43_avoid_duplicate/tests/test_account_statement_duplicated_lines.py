# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.modules.module import get_module_resource
from odoo.tests import common


class AccountStatementDuplicatedLines(common.SavepointCase):
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
        eur_currency = cls.env.ref("base.EUR")
        cls.journal = cls.env["account.journal"].create(
            {
                "type": "bank",
                "name": "Test N43 bank",
                "code": "BNKN43",
                "company_id": cls.env.company.id,
                "bank_account_id": cls.partner_bank.id,
                "currency_id": eur_currency.id,
            }
        )
        n43_file_path = get_module_resource(
            "l10n_es_account_statement_n43_avoid_duplicate", "tests", "test.n43"
        )
        n43_duplicated_path = get_module_resource(
            "l10n_es_account_statement_n43_avoid_duplicate",
            "tests",
            "test_duplicated_lines.n43",
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        n43_duplicated_file = base64.b64encode(open(n43_duplicated_path, "rb").read())
        cls.import_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )
        cls.import_duplicated_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create(
                {
                    "statement_file": n43_duplicated_file,
                    "statement_filename": "Test_duplicated",
                }
            )
        )

    def test_import_duplicated_n43(self):
        self.import_wizard.import_file_button()
        action = self.import_duplicated_wizard.import_file_button()
        id_bank_statement = action["context"]["default_statement_id"]
        bank_statement_id = self.env["account.bank.statement"].browse(id_bank_statement)
        remove_lines_action = self.env["duplicated.n43.wizard"].create(
            {
                "statement_id": id_bank_statement,
                "line_ids": action["context"]["default_line_ids"],
            }
        )
        remove_lines_action.remove_duplicated_lines()
        self.assertTrue(remove_lines_action)
        self.assertTrue(bank_statement_id.line_ids)
        statements = bank_statement_id.line_ids
        statement = statements[0].statement_id
        self.assertEqual(statement.date, fields.Date.to_date("2016-02-01"))
        self.assertEqual(len(statements), 2)
        transactions = """
        <p>12/05/2016 COMISIï¿½N -0.03<br>
        </p>16/05/2016 TRANSFERENC. A TEST PARTNER N43 -178.3
        <br>25/05/2016 TRANSFERENC. TEST PARTNER 2 280.29<br>
        """
        transactions = transactions.strip().replace(" ", "").replace("\n", "")
        # self.assertEqual(statement.removed_transactions.replace(" ", ""), transactions)
        self.assertAlmostEqual(statement.balance_start, 101.96, 2)
        self.assertAlmostEqual(statement.balance_end, 458.56, 2)
