# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64

from odoo import fields
from odoo.modules.module import get_module_resource
from odoo.tests import common


class L10nEsAccountBankStatementImportN43(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(L10nEsAccountBankStatementImportN43, cls).setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.journal = cls.env["account.journal"].create(
            {"type": "bank", "name": "Test N43 bank", "code": "BNKN43"}
        )
        n43_file_path = get_module_resource(
            "l10n_es_account_bank_statement_import_n43", "tests", "test.n43"
        )
        n43_file = base64.b64encode(open(n43_file_path, "rb").read())
        attachment = cls.env["ir.attachment"].create(
            {"datas": n43_file, "name": "N43 File"}
        )
        cls.import_wizard = (
            cls.env["account.bank.statement.import"]
            .with_context(journal_id=cls.journal.id)
            .create({"attachment_ids": [(6, 0, attachment.ids)]})
        )

    def test_import_n43(self):
        action = self.import_wizard.import_file()
        self.assertTrue(action)
        self.assertTrue(action.get("context").get("statement_line_ids"))
        statements = self.env["account.bank.statement.line"].browse(
            action["context"]["statement_line_ids"]
        )
        statement = statements[0].statement_id
        self.assertEqual(statement.date, fields.Date.to_date("2016-02-01"))
        self.assertEqual(len(statements), 3)
        self.assertTrue(statements.filtered(lambda st: str(st.date) == "2016-05-25"))
        self.assertTrue(statements.filtered(lambda st: str(st.date) == "2016-05-16"))
        self.assertTrue(statements.filtered(lambda st: str(st.date) == "2016-05-12"))
        self.assertEqual(statements[0].date, fields.Date.to_date("2016-05-25"))
        self.assertAlmostEqual(statement.balance_start, 0, 2)
        self.assertAlmostEqual(statement.balance_end, 101.96, 2)
        self.assertEqual(statements[1].partner_id, self.partner)

    def test_import_n43_fecha_oper(self):
        self.journal.n43_date_type = "fecha_oper"
        action = self.import_wizard.import_file()
        self.assertTrue(action)
        self.assertTrue(action.get("context").get("statement_line_ids"))
        statements = self.env["account.bank.statement.line"].browse(
            action["context"]["statement_line_ids"]
        )
        self.assertEqual(statements[0].date, fields.Date.to_date("2016-05-26"))
