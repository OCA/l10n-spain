# -*- coding: utf-8 -*-
# © 2016 Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl-3.0).
from openerp.tests import common
from openerp import fields


class TestAccountBalance(common.SavepointCase):

    @classmethod
    def setUpClass(cls):
        super(TestAccountBalance, cls).setUpClass()

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
        cls.company_id = cls.user_obj.browse(cls.env.uid).company_id.id

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
                (0, 0, {'account_id': cls.account_1515.id,
                        'name': 'Basic Payment',
                        'debit': 100.0
                        }),
                (0, 0, {'account_id': cls.account_4545.id,
                        'name': 'Basic Payment',
                        'credit': 100.0
                        }),
            ],
        })
        cls.move100_1_4.post()

        # Duplicate some moves
        cls.move200_1_4 = cls.move100_1_4.copy(default=dict(
            date=fields.Date.today(),
            line_ids=[
                (0, 0, {'account_id': cls.account_1515.id,
                        'name': 'Basic Payment',
                        'debit': 200.0
                        }),
                (0, 0, {'account_id': cls.account_4545.id,
                        'name': 'Basic Payment',
                        'credit': 200.0
                        })
            ],
        ))
        cls.move200_1_4.post()

        # Duplicate some moves
        cls.move75_4_1 = cls.move200_1_4.copy(default=dict(
            line_ids=[
                (0, 0, {'account_id': cls.account_4545.id,
                        'name': 'Basic Charge',
                        'debit': 75.0
                        }),
                (0, 0, {'account_id': cls.account_1515.id,
                        'name': 'Basic Charge',
                        'credit': 75.0
                        })
            ]
        ))
        cls.move75_4_1.post()

        # Duplicate some moves
        cls.move90_6_1 = cls.move200_1_4.copy(default=dict(
            line_ids=[
                (0, 0, {'account_id': cls.account_6565.id,
                        'name': 'Account to account',
                        'debit': 90.0
                        }),
                (0, 0, {'account_id': cls.account_1515.id,
                        'name': 'Account to account',
                        'credit': 90.0
                        })
            ]
        ))
        cls.move90_6_1.post()

        # Create a template Debit-Credit
        cls.template0 = cls.template_obj.create(vals={
            'name': 'test_template debit-credit',
            'balance_mode': '0',
        })
        cls.parent = cls.line_obj.create(vals={
            'name': 'Testing balance template',
            'code': '1100',
            'template_id': cls.template0.id,
            'sequence': 1,
        })
        cls.line_obj.create(vals={
            'name': 'account 1',
            'code': '1200',
            'current_value': '151*',
            'negate': True,
            'parent_id': cls.parent.id,
            'template_id': cls.template0.id,
            'sequence': 2,
        })
        cls.line_obj.create(vals={
            'name': 'account 2',
            'code': '1300',
            'current_value': '454*',
            'negate': False,
            'parent_id': cls.parent.id,
            'template_id': cls.template0.id,
            'sequence': 3,
        })
        cls.line_obj.create(vals={
            'name': 'account 3',
            'code': '1400',
            'current_value': '656*',
            'negate': True,
            'parent_id': cls.parent.id,
            'template_id': cls.template0.id,
            'sequence': 4,
        })
        cls.line_obj.create(vals={
            'name': 'account 4',
            'code': '1500',
            'current_value': '656*',
            'negate': False,
            'parent_id': cls.parent.id,
            'template_id': cls.template0.id,
            'sequence': 5,
        })

        # Create a report with this template
        cls.report0 = cls.reporting_obj.create(vals={
            'name': 'Report 0',
            'template_id': cls.template0.id,
            'company_id': cls.company_id,
            'state': 'draft',
            'current_date_from': fields.Date.today(),
            'current_date_to': fields.Date.today(),
        })

        # Create a template Debit-Credit with brackets
        cls.template1 = cls.template_obj.copy(cls.template0.id,
                                              default=dict(balance_mode='1'))

        # Create a report with this template
        cls.report1 = cls.reporting_obj.copy(cls.report0.id, default={
            'name': 'Report 1',
            'template_id': cls.template1.id,
        })

        # Create a template Credit-Debit
        cls.template2 = cls.template_obj.copy(cls.template0.id,
                                              default=dict(balance_mode='2'))

        # Create a report with this template
        cls.report2 = cls.reporting_obj.copy(cls.report0.id, default={
            'name': 'Report 2',
            'template_id': cls.template2.id,
        })

        # Create a template Credit-Debit reversed with brackets
        cls.template3 = cls.template_obj.copy(cls.template0.id,
                                              default=dict(balance_mode='3'))

        # Create a report with this template
        cls.report3 = cls.reporting_obj.copy(cls.report0.id, default={
            'name': 'Report 3',
            'template_id': cls.template3.id,
        })

    def test_account_balance(self):
        """ Testing account_balance_reporting """

        # Calculate reports
        self.report0.action_calculate()
        self.report1.action_calculate()
        self.report2.action_calculate()
        self.report3.action_calculate()

        # Check results for debit-credit report
        # move_100_1_4 is discarded by date
        line2 = -(200.0 - 75.0 - 90.0)  # It's a negate line
        line3 = -200.0 + 75.0
        line4 = -90.0  # It's a negate line
        line5 = 90.0
        line1 = line2 + line3 + line4 + line5
        for line in self.report0.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            if line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            if line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            if line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            if line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)

        # Check results for debit-credit report with brackets
        # move_100_1_4 is discarded by date
        line2 = (200.0 - 75.0 - 90.0) * -1.0  # It's a negate line
        line3 = -200.0 + 75.0
        line4 = 90.0 * -1.0  # It's a negate line
        line5 = 90.0
        line1 = line2 + line3 + line4 + line5
        for line in self.report1.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            if line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            if line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            if line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            if line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)

        # Check results for credit-dedit report
        # move_100_1_4 is discarded by date
        line2 = (-200.0 + 75.0 + 90.0) * -1.0  # It's a negate line
        line3 = 200.0 - 75.0
        line4 = -90.0 * -1.0  # It's a negate line
        line5 = -90.0
        line1 = line2 + line3 + line4 + line5
        for line in self.report2.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            if line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            if line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            if line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            if line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)

        # Check results for credit-debit report with brackets
        # move_100_1_4 is discarded by date
        line2 = (-200.0 + 75.0 + 90.0) * -1.0  # It's a negate line
        line3 = 200.0 - 75.0
        line4 = -90.0 * -1.0  # It's a negate line
        line5 = -90.0
        line1 = line2 + line3 + line4 + line5
        for line in self.report2.line_ids:
            if line.sequence == 1:
                self.assertAlmostEqual(line1, line.current_value, 2)
            if line.sequence == 2:
                self.assertAlmostEqual(line2, line.current_value, 2)
            if line.sequence == 3:
                self.assertAlmostEqual(line3, line.current_value, 2)
            if line.sequence == 4:
                self.assertAlmostEqual(line4, line.current_value, 2)
            if line.sequence == 5:
                self.assertAlmostEqual(line5, line.current_value, 2)
