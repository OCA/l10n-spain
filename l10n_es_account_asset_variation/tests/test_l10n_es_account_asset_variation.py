# -*- coding: utf-8 -*-
# Copyright 2017 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import openerp.tests.common as common
from openerp import fields


class TestL10nEsAccountAssetVariation(common.TransactionCase):

    def setUp(self):
        super(TestL10nEsAccountAssetVariation, self).setUp()
        self.asset_model = self.env['account.asset.asset']
        self.wiz_obj = self.env['account.asset.variation']
        asset_vals = {
            'name': 'Test Variation Asset',
            'category_id': self.ref('account_asset.account_asset_category_'
                                    'fixedassets0'),
            'code': 'REF01',
            'purchase_date': fields.Date.from_string('2015-01-01'),
            'method': 'linear',
            'purchase_value': 30000,
            'method_time': 'percentage',
            'move_end_period': True,
            'method_number': 10,
            'method_percentage': 10,
            'method_period': 12
            }
        self.asset = self.asset_model.create(asset_vals)

    def test_asset_variation(self):
        self.asset.compute_depreciation_board()
        lines = self.asset.depreciation_line_ids.filtered(
            lambda x: x.amount != 3000)
        self.assertFalse(lines, "The amount of lines is not correct.")
        lines = self.asset.depreciation_line_ids.filtered(
            lambda x: x.method_percentage != 10)
        self.assertFalse(lines, "The percentage of lines is not correct.")
        wiz_vals = {
            'start_date': fields.Date.from_string('2017-01-01'),
            'end_date': fields.Date.from_string('2018-01-01'),
            'percentage': 5,
            }
        wizard = self.wiz_obj.with_context(
            active_model='account.asset.asset', active_id=self.asset.id,
            active_ids=[self.asset.id]).create(wiz_vals)
        wizard.action_calculate_depreciation_board()
        self.assertEqual(
            sum(self.asset.depreciation_line_ids.mapped('amount')), 30000)
        line = self.asset.depreciation_line_ids.filtered(
            lambda x: x.method_percentage == 5)
        self.assertEqual(len(line), 1)
        self.assertEqual(line.amount, 1500)
