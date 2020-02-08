# -*- coding: utf-8 -*-
# Copyright 2016-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.modules.module import get_module_resource


class L10nEsAccountBankStatementImportN43(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(L10nEsAccountBankStatementImportN43, cls).setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Test partner'})
        cls.journal = cls.env['account.journal'].create({
            'type': 'bank',
            'name': 'Test N43 bank',
            'code': 'BNKN43',
        })
        n43_file_path = get_module_resource(
            'l10n_es_account_bank_statement_import_n43', 'tests', 'test.n43')
        n43_file = open(n43_file_path, 'rb').read().encode('base64')
        cls.import_wizard = cls.env['account.bank.statement.import'].create({
            'data_file': n43_file,
        })

    def test_import_n43(self):
        action = self.import_wizard.with_context(
            journal_id=self.journal.id,
        ).import_file()
        self.assertTrue(action)
        self.assertTrue(action.get('context').get('statement_ids'))
        statement = self.env['account.bank.statement'].browse(
            action['context']['statement_ids'][0],
        )
        self.assertEqual(len(statement.line_ids), 3)
        self.assertEqual(statement.line_ids[2].date, '2016-05-25')
        self.assertAlmostEqual(statement.balance_start, 0, 2)
        self.assertAlmostEqual(statement.balance_end, 101.96, 2)
        self.assertEqual(statement.line_ids[1].partner_id, self.partner)

    def test_import_n43_fecha_oper(self):
        self.journal.n43_date_type = 'fecha_oper'
        action = self.import_wizard.with_context(
            journal_id=self.journal.id,
        ).import_file()
        self.assertTrue(action)
        self.assertTrue(action.get('context').get('statement_ids'))
        statement = self.env['account.bank.statement'].browse(
            action['context']['statement_ids'][0],
        )
        self.assertEqual(statement.line_ids[2].date, '2016-05-26')
