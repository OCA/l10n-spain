# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

from odoo.addons.account_balance_reporting.tests.test_account_balance \
    import TestAccountBalanceBase


class TestAccountBalanceReportingXlsx(TestAccountBalanceBase):
    def test_generation_report_xlsx(self):
        report_action = self.print_wizard.xlsx_export()
        report_name = 'account_balance_reporting_xlsx.generic_report'
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'report_type': 'xlsx',
            },
            report_action,
        )
        report_xlsx = self.env.ref(
            'account_balance_reporting_xlsx.'
            'account_balance_reporting_generic_report_xlsx'
        ).render_report(
            self.report.ids, report_name, {
                'report_id': [self.report.id, self.report.name],
                'report_type': 'xlsx',
                'report_xml_id': self.print_wizard.report_xml_id.ids,
            },
        )
        self.assertGreaterEqual(len(report_xlsx[0]), 1)
        self.assertEqual(report_xlsx[1], 'xlsx')
