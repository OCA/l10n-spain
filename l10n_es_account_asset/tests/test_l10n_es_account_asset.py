# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2012-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import odoo.tests.common as common
from odoo import fields


class TestL10nEsAccountAsset(common.TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.asset_model = cls.env["account.asset"]
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test asset journal", "code": "AST", "type": "general"}
        )
        cls.expense_account = cls.env["account.account"].create(
            {
                "name": "Expense test account",
                "code": "EXPTEST",
                "account_type": "expense",
            }
        )
        cls.depreciation_account = cls.env["account.account"].create(
            {
                "name": "Depreciation test account",
                "code": "DEPTEST",
                "account_type": "asset_current",
            }
        )
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "name": "Test asset category",
                "account_expense_depreciation_id": cls.expense_account.id,
                "account_asset_id": cls.depreciation_account.id,
                "account_depreciation_id": cls.depreciation_account.id,
                "journal_id": cls.journal.id,
                "method_number": 3,
            }
        )
        cls.asset = cls.asset_model.create(
            {
                "name": "Test Asset",
                "profile_id": cls.profile.id,
                "code": "REF01",
                "date_start": "2015-01-01",
                "method": "linear",
                "purchase_value": 30000,
                "method_time": "percentage",
                "method_percentage": 20,
                "method_period": "year",
            }
        )

    def test_not_prorated_percentage_asset(self):
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 6)
        lines = self.asset.depreciation_line_ids[1:].filtered(
            lambda x: x.amount != 6000
        )
        self.assertFalse(lines, "The amount of lines is not correct.")

    def test_prorated_percentage_asset(self):
        self.asset.write(
            {"prorata": True, "date_start": fields.Date.to_date("2015-04-10")}
        )
        self.asset.compute_depreciation_board()
        self.assertEqual(
            self.asset.depreciation_line_ids[1].amount,
            4372.6,
            "First depreciation amount is not correct.",
        )
        lines = self.asset.depreciation_line_ids[2:-2].filtered(
            lambda x: x.amount != 6000
        )
        self.assertFalse(lines, "The amount of lines is not correct.")
        self.assertEqual(
            self.asset.depreciation_line_ids[-1:].amount,
            1627.4,
            "Last depreciation amount is not correct.",
        )

    def test_prorated_percentage_asset_different_years(self):
        self.asset.write(
            {
                "prorata": True,
                "method_percentage": 70,
                "date_start": fields.Date.to_date("2017-11-15"),
            }
        )
        self.asset.compute_depreciation_board()
        self.assertGreater(
            self.asset.depreciation_line_ids[-1:].amount,
            0,
            "Last depreciation amount is not correct.",
        )

    def test_asset_other_percentage(self):
        """Test for regression detected for annual percentage lower than 20."""
        self.asset.annual_percentage = 10
        # Check computed field
        self.assertEqual(self.asset.method_percentage, 10)
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 11)
        lines = self.asset.depreciation_line_ids[1:].filtered(
            lambda x: x.amount != 3000
        )
        self.assertFalse(lines, "The amount of lines is not correct.")

    def test_assign_profile(self):
        # direct profile assignation
        profile = self.profile.copy(
            {
                "name": "Test asset category percentage",
                "method_time": "percentage",
                "method_percentage": 20,
                "method_period": "year",
            }
        )
        self.asset.profile_id = profile
        self.assertEqual(self.asset.method_time, "percentage")
        self.assertEqual(self.asset.annual_percentage, 20)
        # asset creation
        asset = self.asset_model.create(
            {
                "name": "Test Asset 2",
                "profile_id": profile.id,
                "date_start": "2015-01-01",
                "purchase_value": 30000,
            }
        )
        self.assertEqual(asset.method_time, "percentage")
        self.assertEqual(asset.annual_percentage, 20)
        # asset copy
        asset = self.asset.copy({"profile_id": profile.id})
        self.assertEqual(asset.method_time, "percentage")
        self.assertEqual(asset.annual_percentage, 20)

    def test_asset_other_method(self):
        """Test for regression detected using other time methods."""
        self.asset.method_time = "year"
        self.asset.method_number = 8
        self.asset.compute_depreciation_board()
        self.assertEqual(len(self.asset.depreciation_line_ids), 9)
