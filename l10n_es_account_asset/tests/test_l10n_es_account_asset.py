# -*- coding: utf-8 -*-
# (c) 2015 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common
from openerp import fields
import calendar


class TestL10nEsAccountAsset(common.TransactionCase):

    def setUp(self):
        super(TestL10nEsAccountAsset, self).setUp()
        self.asset_model = self.env['account.asset.asset']
        asset_vals = {
            'name': 'Test Asset',
            'category_id': self.ref('account_asset.account_asset_category_'
                                    'fixedassets0'),
            'code': 'REF01',
            'purchase_date': fields.Date.from_string('2015-01-01'),
            'method': 'linear',
            'purchase_value': 30000,
            'ext_method_time': 'number',
            'move_end_period': True,
            'method_number': 10,
            'method_period': 1
            }
        self.asset_linear = self.asset_model.create(asset_vals)
        asset_vals['ext_method_time'] = 'percentage'
        asset_vals['method_percentage'] = 20
        self.asset_percentage = self.asset_model.create(asset_vals)

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
