# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

from odoo import exceptions

from odoo.addons.l10n_es_aeat_vat_prorrate.tests.test_l10n_es_vat_prorrate import (
    TestL10nEsAeatVatProrrateBase,
)


class TestL10nEsAeatVatProrrateAsset(TestL10nEsAeatVatProrrateBase):
    def setUp(self):
        super().setUp()
        self.asset_profile = self.env["account.asset.profile"].create(
            {
                "name": "Test asset profile",
                "account_asset_id": self.counterpart_account.id,
                "account_depreciation_id": self.counterpart_account.id,
                "account_expense_depreciation_id": self.counterpart_account.id,
                "journal_id": self.journal.id,
            }
        )
        self.invoice_asset = (
            self.env["account.move"]
            .with_user(self.billing_user)
            .create(
                {
                    "company_id": self.company.id,
                    "partner_id": self.customer.id,
                    "invoice_date": "2017-01-01",
                    "type": "in_invoice",
                    "journal_id": self.journal_purchase.id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "name": "Test for asset",
                                "account_id": self.accounts["700000"].id,
                                "price_unit": 100,
                                "quantity": 1,
                                "tax_ids": [
                                    (4, t.id) for t in self._get_taxes("P_IVA21_BC")
                                ],
                                "asset_profile_id": self.asset_profile.id,
                                "vat_prorrate_percent": 80,
                            },
                        )
                    ],
                }
            )
        )
        all_assets = self.env["account.asset"].search([])
        self.invoice_asset.action_post()
        current_assets = self.env["account.asset"].search([])
        self.asset = current_assets - all_assets

    def test_vat_prorrate_asset(self):
        # Check constraint
        with self.assertRaises(exceptions.ValidationError):
            self.invoice_asset.invoice_line_ids.vat_prorrate_percent = -0.01
        with self.assertRaises(exceptions.ValidationError):
            self.invoice_asset.invoice_line_ids.vat_prorrate_percent = 100.1
        # Check asset creation values
        self.assertAlmostEqual(self.asset.purchase_value, 104.2)
        self.assertAlmostEqual(self.asset.vat_prorrate_percent, 80)
        self.assertAlmostEqual(self.asset.vat_prorrate_increment, 4.2)
        # Check casilla 44 variation
        self.model303.unlink()  # unlink this for not distorting
        self.model303_4t.vat_prorrate_percent = 87
        self.model303_4t.button_calculate()
        self.assertAlmostEqual(self.model303_4t.casilla_44, 1.47)
