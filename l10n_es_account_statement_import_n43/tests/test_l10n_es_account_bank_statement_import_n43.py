# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.modules.module import get_module_resource
from odoo.tests import common


class L10nEsAccountStatementImportN43(common.SavepointCase):
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
            "l10n_es_account_statement_import_n43", "tests", "test.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        cls.import_wizard = (
            cls.env["account.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"statement_file": n43_file, "statement_filename": "Test"})
        )

    def test_import_n43(self):
        action = self.import_wizard.import_file_button()
        self.assertTrue(action)
        statements = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        statement = statements[2].statement_id
        self.assertEqual(statement.date, fields.Date.to_date("2016-02-01"))
        self.assertEqual(len(statements), 3)
        self.assertTrue(statements.filtered(lambda st: str(st.date) == "2016-05-25"))
        self.assertTrue(statements.filtered(lambda st: str(st.date) == "2016-05-16"))
        self.assertTrue(statements.filtered(lambda st: str(st.date) == "2016-05-12"))
        self.assertEqual(statements[2].date, fields.Date.to_date("2016-05-25"))
        self.assertAlmostEqual(statement.balance_start, 0, 2)
        self.assertAlmostEqual(statement.balance_end, 101.96, 2)
        self.assertEqual(statements[0].partner_id, self.partner)

    def test_import_n43_fecha_oper(self):
        self.journal.n43_date_type = "fecha_oper"
        action = self.import_wizard.import_file_button()
        self.assertTrue(action)
        statements = self.env["account.bank.statement.line"].search(
            [("statement_id.journal_id", "=", self.journal.id)]
        )
        self.assertEqual(statements[2].date, fields.Date.to_date("2016-05-26"))
