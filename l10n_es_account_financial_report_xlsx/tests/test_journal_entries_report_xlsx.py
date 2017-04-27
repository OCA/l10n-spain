# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import exceptions
from openerp.addons.l10n_es_account_financial_report.tests.\
    test_journal_entries_report import BaseTestJournalEntriesReport


class TestJournalEntriesReportXlsx(BaseTestJournalEntriesReport):
    @classmethod
    def setUpClass(cls):
        super(TestJournalEntriesReportXlsx, cls).setUpClass()
        cls.xlsx_report_name = (
            'l10n_es_account_financial_report.journal_entries_xlsx'
        )
        cls.xlsx_action_name = (
            'l10n_es_account_financial_report_xlsx.'
            'account_journal_entries_report_xlsx'
        )

    def test_no_data(self):
        self.wizard.period_ids = False
        with self.assertRaises(exceptions.Warning):
            self.wizard.print_report_xlsx()

    def test_report_action(self):
        report_action = self.wizard.print_report_xlsx()
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': self.xlsx_report_name,
                'report_type': 'xlsx',
            },
            report_action,
        )

    def test_check_xlsx_generation(self):
        report_xlsx = self.env.ref(self.xlsx_action_name).render_report(
            self.wizard.ids,
            self.xlsx_report_name,
            {
                'journal_ids': self.journal.ids,
                'period_ids': self.period.ids,
            },
        )
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
