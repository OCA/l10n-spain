# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2012-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import odoo.tests.common as common
from odoo import fields


class TestL10nEsAccountAsset(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAccountAsset, cls).setUpClass()
        cls.asset_model = cls.env['account.asset']
        cls.journal = cls.env['account.journal'].create({
            'name': 'Test asset journal',
            'code': 'AST',
            'type': 'general',
        })
        cls.account_type = cls.env['account.account.type'].create({
            'name': 'Test account type',
            'type': 'other',
        })
        cls.expense_account = cls.env['account.account'].create({
            'name': 'Expense test account',
            'code': 'EXP_TEST',
            'user_type_id': cls.account_type.id,
        })
        cls.depreciation_account = cls.env['account.account'].create({
            'name': 'Depreciation test account',
            'code': 'DEP_TEST',
            'user_type_id': cls.account_type.id,
        })
        cls.profile = cls.env['account.asset.profile'].create({
            'name': 'Test asset category',
            'account_expense_depreciation_id': cls.expense_account.id,
            'account_asset_id': cls.depreciation_account.id,
            'account_depreciation_id': cls.depreciation_account.id,
            'journal_id': cls.journal.id,
            'method_number': 3,
        })
        cls.asset = cls.asset_model.create({
            'name': 'Test Asset',
            'profile_id': cls.profile.id,
            'code': 'REF01',
            'date_start': '2015-01-01',
            'method': 'linear',
            'purchase_value': 30000,
            'method_time': 'percentage',
            'method_percentage': 20,
            'method_period': 'year',
        })

    def test_not_prorated_percentage_asset(self):
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 6)
        lines = self.asset.depreciation_line_ids[1:].filtered(
            lambda x: x.amount != 6000)
        self.assertFalse(lines, "The amount of lines is not correct.")

    def test_prorated_percentage_asset(self):
        self.asset.write({
            'prorata': True,
            'date_start': fields.Date.to_date('2015-04-10'),
        })
        self.asset.compute_depreciation_board()
        self.assertEqual(
            self.asset.depreciation_line_ids[1].amount, 4372.6,
            "First depreciation amount is not correct.")
        lines = self.asset.depreciation_line_ids[2:-2].filtered(
            lambda x: x.amount != 6000)
        self.assertFalse(lines, "The amount of lines is not correct.")
        self.assertEqual(
            self.asset.depreciation_line_ids[-1:].amount, 1627.4,
            "Last depreciation amount is not correct.")

    def test_prorated_percentage_asset_different_years(self):
        self.asset.write({
            'prorata': True,
            'method_percentage': 70,
            'date_start': fields.Date.to_date('2017-11-15'),
        })
        self.asset.compute_depreciation_board()
        self.assertGreater(
            self.asset.depreciation_line_ids[-1:].amount, 0,
            "Last depreciation amount is not correct.")
