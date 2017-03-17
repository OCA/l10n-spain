# -*- coding: utf-8 -*-
# © 2016 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.tests import common
from odoo.modules.module import get_module_resource


class L10nEsAccountBankStatementImportN43(common.TransactionCase):
    def setUp(self):
        super(L10nEsAccountBankStatementImportN43, self).setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test partner'})
        self.journal = self.env['account.journal'].create({
            'type': 'bank',
            'name': 'Test N43 bank',
            'code': 'BNKN43',
        })

    def test_import_n43(self):
        n43_file_path = get_module_resource(
            'l10n_es_account_bank_statement_import_n43', 'tests', 'test.n43')
        n43_file = open(n43_file_path, 'rb').read().encode('base64')
        import_wizard = self.env['account.bank.statement.import'].create({
            'data_file': n43_file,
        })
        action = import_wizard.with_context(
            journal_id=self.journal.id,
        ).import_file()
        self.assertTrue(action)
        self.assertTrue(action.get('context').get('statement_ids'))
        statement = self.env['account.bank.statement'].browse(
            action['context']['statement_ids'][0])
        self.assertEqual(len(statement.line_ids), 3)
        self.assertAlmostEqual(statement.balance_start, 0, 2)
        self.assertAlmostEqual(statement.balance_end, 101.96, 2)
        self.assertEqual(statement.line_ids[1].partner_id, self.partner)
