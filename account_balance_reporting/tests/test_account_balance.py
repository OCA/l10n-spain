# -*- coding: utf-8 -*-
# Copyright 2016 Tecnativa - Vicent Cubells <vicent.cubells@tecnativa.com>
# Copyright 2016-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).

from openerp.tests import common
from openerp import fields


class TestAccountBalanceBase(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestAccountBalanceBase, cls).setUpClass()
        # Environments
        cls.account_obj = cls.env['account.account']
        cls.type_obj = cls.env['account.account.type']
        cls.user_obj = cls.env['res.users']
        cls.move_obj = cls.env['account.move']
        cls.journal_obj = cls.env['account.journal']
        cls.template_obj = cls.env['account.balance.reporting.template']
        cls.reporting_obj = cls.env['account.balance.reporting']
        cls.line_obj = cls.env['account.balance.reporting.template.line']
        cls.reporting_line_obj = cls.env['account.balance.reporting.line']
        # Instance: company
        cls.company_id = cls.env.user.company_id.id
        # Account Types
        cls.account_user_type = cls.type_obj.create(vals=dict(
            name='other',
        ))
        # Accounts
        cls.account_1515 = cls.account_obj.create(vals=dict(
            name='Account 1515',
            company_id=cls.company_id,
            code='151500',
            user_type_id=cls.account_user_type.id,
            reconcile=True,
        ))
        cls.account_4545 = cls.account_obj.create(vals=dict(
            name='Account 4545',
            company_id=cls.company_id,
            code='454500',
            user_type_id=cls.account_user_type.id,
            reconcile=True,
        ))
        cls.account_6565 = cls.account_obj.create(vals=dict(
            name='Account 6565',
            company_id=cls.company_id,
            code='656500',
            user_type_id=cls.account_user_type.id,
            reconcile=True,
        ))
        # Journal
        cls.journal = cls.journal_obj.create(vals={
            'name': 'Bank Journal Test',
            'type': 'bank',
            'code': 'BKTEST',
            'default_debit_account_id': cls.account_1515.id,
            'default_credit_account_id': cls.account_1515.id,
        })
        # Account moves
        # Initial dummy account move to be discarded by date
        cls.move100_1_4 = cls.move_obj.create(vals={
            'name': '/',
            'ref': '2011010',
            'journal_id': cls.journal.id,
            'state': 'draft',
            'company_id': cls.company_id,
            'date': fields.Date.from_string('2016-01-01'),
            'line_ids': [
                (0, 0, {
                    'account_id': cls.account_1515.id,
                    'name': 'Basic Payment',
                    'debit': 100.0,
                }),
                (0, 0, {
                    'account_id': cls.account_4545.id,
                    'name': 'Basic Payment',
                    'credit': 100.0,
                }),
            ],
        })
        cls.move100_1_4.post()
        # Duplicate some moves
        cls.move200_1_4 = cls.move100_1_4.copy(default=dict(
            date=fields.Date.today(),
            line_ids=[
                (0, 0, {
                    'account_id': cls.account_1515.id,
                    'name': 'Basic Payment',
                    'debit': 200.0,
                }),
                (0, 0, {
                    'account_id': cls.account_4545.id,
                    'name': 'Basic Payment',
                    'credit': 200.0,
                }),
            ],
        ))
        cls.move200_1_4.post()
        # Duplicate some moves
        cls.move75_4_1 = cls.move200_1_4.copy(default=dict(
            line_ids=[
                (0, 0, {
                    'account_id': cls.account_4545.id,
                    'name': 'Basic Charge',
                    'debit': 75.0,
                }),
                (0, 0, {
                    'account_id': cls.account_1515.id,
                    'name': 'Basic Charge',
                    'credit': 75.0,
                }),
            ]
        ))
        cls.move75_4_1.post()
        # Duplicate some moves
        cls.move90_6_1 = cls.move200_1_4.copy(default=dict(
            line_ids=[
                (0, 0, {
                    'account_id': cls.account_6565.id,
                    'name': 'Account to account',
                    'debit': 90.0,
                }),
                (0, 0, {
                    'account_id': cls.account_1515.id,
                    'name': 'Account to account',
                    'credit': 90.0,
                }),
            ]
        ))
        cls.move90_6_1.post()
        # Create a template Debit-Credit
        cls.template = cls.template_obj.create(vals={
            'name': 'test_template debit-credit',
            'balance_mode': '0',
        })
        cls.parent = cls.line_obj.create(vals={
            'name': 'Testing balance template',
            'code': '1100',
            'template_id': cls.template.id,
            'sequence': 1,
        })
        cls.line2 = cls.line_obj.create(vals={
            'name': 'account 1',
            'code': '1200',
            'current_value': '151*',
            'negate': True,
            'parent_id': cls.parent.id,
            'template_id': cls.template.id,
            'sequence': 2,
        })
        cls.line3 = cls.line_obj.create(vals={
            'name': 'account 2',
            'code': '1300',
            'current_value': '454*',
            'negate': False,
            'parent_id': cls.parent.id,
            'template_id': cls.template.id,
            'sequence': 3,
        })
        cls.line4 = cls.line_obj.create(vals={
            'name': 'account 3',
            'code': '1400',
            'current_value': '656*',
            'negate': True,
            'parent_id': cls.parent.id,
            'template_id': cls.template.id,
            'sequence': 4,
        })
        cls.line5 = cls.line_obj.create(vals={
            'name': 'account 4',
            'code': '1500',
            'current_value': '(656*)',
            'negate': False,
            'parent_id': cls.parent.id,
            'template_id': cls.template.id,
            'sequence': 5,
        })
        cls.line6 = cls.line_obj.create(vals={
            'name': 'Sum of accounts',
            'code': '1600',
            'current_value': '1400 + 1500',
            'negate': False,
            'template_id': cls.template.id,
            'sequence': 6,
        })
        # Create a report with this template
        cls.report = cls.reporting_obj.create(vals={
            'name': 'Report 0',
            'template_id': cls.template.id,
            'company_id': cls.company_id,
            'state': 'draft',
            'current_date_from': fields.Date.today(),
            'current_date_to': fields.Date.today(),
        })
        cls.date_range_type = cls.env['date.range.type'].create({
            'name': 'Test range type',
        })
        cls.date_range = cls.env['date.range'].create({
            'name': 'Test date range',
            'type_id': cls.date_range_type.id,
            'date_start': '2017-01-01',
            'date_end': '2017-12-31',
        })
        cls.print_wizard = (
            cls.env['account.balance.reporting.print.wizard'].create({
                'report_id': cls.report.id,
                'report_xml_id': cls.env.ref(
                    'account_balance_reporting.'
                    'report_account_balance_reporting_generic'
                ).id,
            })
        )


class TestAccountBalance(TestAccountBalanceBase):
    def test_onchange_current_date_range(self):
        with self.env.do_in_onchange():
            report = self.env['account.balance.reporting'].new({
                'current_date_range': self.date_range.id,
            })
            report.onchange_current_date_range()
            self.assertEqual(report.current_date_from, '2017-01-01')
            self.assertEqual(report.current_date_to, '2017-12-31')

    def test_onchange_previous_date_range(self):
        with self.env.do_in_onchange():
            report = self.env['account.balance.reporting'].new({
                'previous_date_range': self.date_range.id,
            })
            report.onchange_previous_date_range()
            self.assertEqual(report.previous_date_from, '2017-01-01')
            self.assertEqual(report.previous_date_to, '2017-12-31')

    def test_flow(self):
        self.assertEqual(self.report.state, 'draft')
        self.report.action_calculate()
        self.assertEqual(self.report.state, 'calc_done')
        self.assertTrue(self.report.calc_date)
        line1 = self.report.line_ids.filtered(lambda x: x.sequence == 1)
        self.assertEqual(line1.current_move_line_count, 6)
        self.assertEqual(line1.previous_move_line_count, 0)
        self.report.action_confirm()
        self.assertEqual(self.report.state, 'done')
        self.report.action_cancel()
        self.assertEqual(self.report.state, 'canceled')
        self.report.action_recover()
        self.assertEqual(self.report.state, 'draft')
        self.assertFalse(self.report.calc_date)

    def test_copy_template(self):
        copied_template = self.template.copy()
        self.assertEqual(len(copied_template.line_ids), 6)

    def test_account_balance_mode_0(self):
        """ Check results for debit-credit report. """
        self.report.action_calculate()
        # move_100_1_4 is discarded by date
        line2 = (200.0 - 75.0 - 90.0) * -1.0  # It's a negate line
        line3 = -200.0 + 75.0
        line4 = 90.0 * -1.0  # It's a negate line
        line5 = 90.0
        line6 = line4 + line5
        line1 = line2 + line3 + line4 + line5
        for line in self.report.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
                pass
            elif line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            elif line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            elif line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            elif line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)
            elif line.sequence == 6:
                self.assertAlmostEqual(line6, line.current_value, 2)

    def test_account_balance_mode_1(self):
        """Check results for debit-credit report with brackets."""
        self.template.balance_mode = '1'
        self.report.action_calculate()
        line2 = (200.0 - 75.0 - 90.0) * -1.0  # It's a negate line
        line3 = -200.0 + 75.0
        line4 = 90.0 * -1.0  # It's a negate line
        line5 = -90.0  # Has brackets
        line6 = line4 + line5
        line1 = line2 + line3 + line4 + line5
        for line in self.report.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            elif line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            elif line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            elif line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            elif line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)
            elif line.sequence == 6:
                self.assertAlmostEqual(line6, line.current_value, 2)

    def test_account_balance_mode_2(self):
        """Check results for credit-debit report."""
        self.template.balance_mode = '2'
        self.report.action_calculate()
        line2 = (-200.0 + 75.0 + 90.0) * -1.0  # It's a negate line
        line3 = 200.0 - 75.0
        line4 = -90.0 * -1.0  # It's a negate line
        line5 = -90.0
        line6 = line4 + line5
        line1 = line2 + line3 + line4 + line5
        for line in self.report.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            elif line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            elif line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            elif line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            elif line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)
            elif line.sequence == 6:
                self.assertAlmostEqual(line6, line.current_value, 2)

    def test_account_balance_mode_3(self):
        """Check results for credit-debit report with brackets."""
        self.template.balance_mode = '3'
        self.report.action_calculate()
        line2 = (200.0 - 75.0 - 90.0) * -1.0  # It's a negate line
        line3 = -200.0 + 75.0
        line4 = 90.0 * -1.0  # It's a negate line
        line5 = 90.0 * -1  # Has brackets
        line6 = line4 + line5
        line1 = line2 + line3 + line4 + line5
        for line in self.report.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            elif line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            elif line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            elif line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            elif line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)
            elif line.sequence == 6:
                self.assertAlmostEqual(line6, line.current_value, 2)

    def test_generation_report_qweb(self):
        report_action = self.print_wizard.print_report()
        report_name = 'account_balance_reporting.report_generic'
        self.assertDictContainsSubset(
            {
                'type': 'ir.actions.report.xml',
                'report_name': report_name,
                'datas': {
                    'ids': self.report.ids,
                },
            },
            report_action,
        )
        # Check if report template is correct
        report_html = self.env['report'].get_html(self.report.id, report_name)
        self.assertIn('<tbody class="balance_reporting">', report_html)
