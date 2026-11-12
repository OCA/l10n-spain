# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command

from odoo.addons.l10n_es_aeat.tests.test_l10n_es_aeat_mod_base import (
    TestL10nEsAeatModBase,
)


class TestCreateAssetFromInvoice(TestL10nEsAeatModBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test partner"})
        cls.product = cls.env["product.product"].create({"name": "Test product"})
        cls.journal = cls.env["account.journal"].create(
            {"name": "Test asset journal", "code": "TSTA", "type": "general"}
        )
        cls.profile = cls.env["account.asset.profile"].create(
            {
                "name": "Test asset category",
                "account_expense_depreciation_id": cls.env.ref(
                    f"account.{cls.company.id}_account_common_681"
                ).id,
                "account_asset_id": cls.env.ref(
                    f"account.{cls.company.id}_account_common_213"
                ).id,
                "account_depreciation_id": cls.env.ref(
                    f"account.{cls.company.id}_account_common_2813"
                ).id,
                "journal_id": cls.journal.id,
                "method_number": 3,
            }
        )
        tax = cls.env.ref(f"account.{cls.company.id}_account_tax_template_p_iva0_nd")
        line_vals = {
            "product_id": cls.product.id,
            "name": "Test line",
            "price_unit": 54.23,
            "account_id": cls.profile.account_asset_id.id,
            "asset_profile_id": cls.profile.id,
            "quantity": 1,
            "tax_ids": [Command.link(tax.id)],
        }
        line_vals2 = line_vals.copy()
        line_vals2["price_unit"] = 114.67
        invoice_vals = {
            "company_id": cls.company.id,
            "partner_id": cls.partner.id,
            "invoice_date": "2025-11-01",
            "move_type": "in_invoice",
            "invoice_line_ids": [Command.create(line_vals), Command.create(line_vals2)],
        }
        cls.invoice = cls.env["account.move"].create(invoice_vals)

    def _post_bill(self, lines, move_type="in_invoice", currency=None):
        """Post a vendor bill with one asset line per (price, tax) given"""
        line_vals = []
        for price_unit, tax_xmlid in lines:
            tax = self.env.ref(
                f"account.{self.company.id}_account_tax_template_{tax_xmlid}"
            )
            line_vals.append(
                Command.create(
                    {
                        "product_id": self.product.id,
                        "name": "Test line",
                        "price_unit": price_unit,
                        "account_id": self.profile.account_asset_id.id,
                        "asset_profile_id": self.profile.id,
                        "quantity": 1,
                        "tax_ids": [Command.set(tax.ids)],
                    }
                )
            )
        bill = self.env["account.move"].create(
            {
                "partner_id": self.partner.id,
                "invoice_date": "2025-11-01",
                "move_type": move_type,
                "currency_id": (currency or self.company.currency_id).id,
                "invoice_line_ids": line_vals,
            }
        )
        bill.action_post()
        return bill.invoice_line_ids.asset_id

    def test_create_asset_from_invoice_non_deductible(self):
        self.invoice.action_post()
        lines = self.invoice.invoice_line_ids
        self.assertEqual(lines[0].asset_id.purchase_value, 65.62)  # 54.23 * 1.21
        self.assertEqual(lines[1].asset_id.purchase_value, 138.75)  # 114.67 * 1.21

    def test_group_of_taxes(self):
        """An import of goods with the group of taxes of the DUA"""
        asset = self._post_bill([(100, "p_iva21_ibc_group")])
        self.assertEqual(asset.purchase_value, 100)
