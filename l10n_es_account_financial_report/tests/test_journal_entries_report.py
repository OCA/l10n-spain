# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import exceptions, fields
from openerp.tests import common


class BaseTestJournalEntriesReport(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(BaseTestJournalEntriesReport, cls).setUpClass()
        # Make sure there's at least one journal entry
        cls.fy = cls.env['account.fiscalyear'].create({
            'name': 'Test',
            'code': 'T',
            'date_start': fields.Date.today(),
            'date_stop': fields.Date.today(),
        })
        cls.period = cls.env['account.period'].create({
            'name': 'Test period',
            'fiscalyear_id': cls.fy.id,
            'special': True,  # for avoiding overlapping periods
            'date_start': fields.Date.today(),
            'date_stop': fields.Date.today(),
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test account type',
            'code': 'TEST',
            'report_type': 'none',
            'close_method': 'none',
        })
        cls.account = cls.env['account.account'].create({
            'name': 'Test account',
            'code': 'TEST',
            'type': 'other',
            'user_type': cls.account_type.id,
        })
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test journal',
            'code': 'TEST',
            'type': 'general',
        })
        cls.move = cls.env['account.move'].create({
            'journal_id': cls.journal.id,
            'period_id': cls.period.id,
            'date': fields.Date.today(),
            'line_id': [
                (0, 0, {
                    'name': 'Debit line',
                    'account_id': cls.account.id,
                    'debit': 100,
                }),
                (0, 0, {
                    'name': 'Credit line',
                    'account_id': cls.account.id,
                    'credit': 100,
                }),
            ],
        })
        cls.move.button_validate()
        cls.wizard = cls.env['account.journal.entries.report'].create({
            'period_ids': [
                (6, 0, cls.env['account.period'].search([
                    ('company_id', '=', cls.env.user.company_id.id),
                ]).ids),
            ],
            'journal_ids': [(6, 0, cls.journal.ids)],
        })


class TestJournalEntriesReport(BaseTestJournalEntriesReport):
    @classmethod
    def setUpClass(cls):
        super(TestJournalEntriesReport, cls).setUpClass()
        cls.report_name = 'l10n_es_account_financial_report.journal_entries'
        cls.action_name = (
            'l10n_es_account_financial_report.account_journal_entries_report'
        )

    def test_no_data(self):
        self.wizard.period_ids = False
        with self.assertRaises(exceptions.Warning):
            self.wizard.print_report()

    def test_report_action(self):
        report_action = self.wizard.print_report()
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': self.report_name,
                'report_type': 'qweb-pdf',
            },
            report_action,
        )

    def test_check_pdf_generation(self):
        report_qweb = self.env.ref(self.action_name).render_report(
            self.wizard.ids,
            self.report_name,
            {
                'journal_ids': self.journal.ids,
                'period_ids': self.period.ids,
            },
        )
        self.assertGreaterEqual(len(report_qweb[0]), 1)
        self.assertEqual(report_qweb[1], 'html')
