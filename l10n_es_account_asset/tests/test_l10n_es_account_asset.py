# -*- coding: utf-8 -*-
# Copyright 2015 Ainara Galdona - AvanzOSC
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2012-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import odoo.tests.common as common
from odoo import fields
import calendar


class TestL10nEsAccountAsset(common.SavepointCase):
    @classmethod
    def setUpClass(cls):
        super(TestL10nEsAccountAsset, cls).setUpClass()
        cls.asset_model = cls.env['account.asset.asset']
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
        cls.category = cls.env['account.asset.category'].create({
            'name': 'Test asset category',
            'account_depreciation_expense_id': cls.expense_account.id,
            'account_asset_id': cls.depreciation_account.id,
            'account_depreciation_id': cls.depreciation_account.id,
            'journal_id': cls.journal.id,
            'method_number': 3,
        })
        asset_number_vals = {
            'name': 'Test Asset',
            'category_id': cls.category.id,
            'code': 'REF01',
            'date': '2015-01-01',
            'method': 'linear',
            'value': 30000,
            'method_time': 'number',
            'move_end_period': True,
            'method_number': 10,
            'method_period': 1,
        }
        asset_percentage_vals = asset_number_vals.copy()
        asset_percentage_vals['method_time'] = 'percentage'
        asset_percentage_vals['method_percentage'] = 20
        cls.asset_linear = cls.asset_model.create(asset_number_vals)
        cls.asset_percentage = cls.asset_model.create(asset_percentage_vals)

    def test_not_prorated_linear_asset(self):
        self.asset_linear.compute_depreciation_board()
        lines = self.asset_linear.depreciation_line_ids.filtered(
            lambda x: x.amount != 3000)
        self.assertFalse(lines, "The amount of lines is not correct.")

    def test_prorated_linear_asset(self):
        self.asset_linear.write(
            {'prorata': True,
             'start_depreciation_date': fields.Date.from_string('2015-04-10')})
        self.asset_linear.compute_depreciation_board()
        self.assertEqual(self.asset_linear.depreciation_line_ids[:1].amount,
                         2100, "First depreciation amount is not correct.")
        lines = self.asset_linear.depreciation_line_ids[1:-2].filtered(
            lambda x: x.amount != 3000)
        self.assertFalse(lines, "The amount of lines is not correct.")
        self.assertEqual(self.asset_linear.depreciation_line_ids[-1:].amount,
                         900, "Last depreciation amount is not correct.")

    def test_not_prorated_percentage_asset(self):
        self.asset_percentage.compute_depreciation_board()
        lines = self.asset_percentage.depreciation_line_ids.filtered(
            lambda x: x.amount != 6000)
        self.assertFalse(lines, "The amount of lines is not correct.")

    def test_prorated_percentage_asset(self):
        self.asset_percentage.write(
            {'prorata': True,
             'start_depreciation_date': fields.Date.from_string('2015-04-10')})
        self.asset_percentage.compute_depreciation_board()
        self.assertEqual(
            self.asset_percentage.depreciation_line_ids[:1].amount, 4200,
            "First depreciation amount is not correct.")
        lines = self.asset_percentage.depreciation_line_ids[1:-2].filtered(
            lambda x: x.amount != 6000)
        self.assertFalse(lines, "The amount of lines is not correct.")
        self.assertEqual(
            self.asset_percentage.depreciation_line_ids[-1:].amount, 1800,
            "Last depreciation amount is not correct.")

    def test_move_end_period_asset(self):
        self.asset_percentage.compute_depreciation_board()
        for line in self.asset_percentage.depreciation_line_ids:
            line_date = fields.Date.from_string(line.depreciation_date)
            self.assertEqual(
                line_date.day,
                calendar.monthrange(line_date.year, line_date.month)[1],
                "Depreciation date is not the end of period.")

    def test_prorated_percentage_asset_different_years(self):
        start_depreciation_date = fields.Date.from_string('2017-11-15')
        self.asset_percentage.write(
            {'prorata': True,
             'method_percentage': 70,
             'start_depreciation_date': start_depreciation_date})
        self.asset_linear.write(
            {'date': '2017-11-15',
             'method_time': 'percentage'})
        self.asset_percentage.compute_depreciation_board()
        self.assertGreater(
            self.asset_percentage.depreciation_line_ids[-1:].amount, 0,
            "Last depreciation amount is not correct.")
