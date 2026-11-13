# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import Command
from odoo.tests import Form

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
        # A currency rounded to units
        cls.jpy = cls.env.ref("base.JPY")
        cls.jpy.active = True
        cls.env["res.currency.rate"].create(
            {
                "name": "2025-11-01",
                "rate": 150,
                "currency_id": cls.jpy.id,
                "company_id": cls.company.id,
            }
        )
        # Cars, on an account with an asset profile
        cls.car_account = cls.env.ref(f"account.{cls.company.id}_account_common_218")
        cls.car_profile = cls.profile.copy(
            {"name": "Cars", "account_asset_id": cls.car_account.id}
        )
        cls.car_account.asset_profile_id = cls.car_profile

    def _post_bill_form(self, lines):
        """Post a vendor bill entered in its form, with one line on the cars
        account per (price, tax, deductible percentage) given"""
        bill_form = Form(
            self.env["account.move"]
            .with_user(self.account_user)
            .with_context(default_move_type="in_invoice")
        )
        bill_form.partner_id = self.supplier
        bill_form.invoice_date = "2025-11-01"
        bill_form.journal_id = self.journal_purchase
        for price_unit, tax_xmlid, deductible_percentage in lines:
            with bill_form.invoice_line_ids.new() as line_form:
                line_form.name = "Car"
                line_form.account_id = self.car_account
                line_form.price_unit = price_unit
                line_form.tax_ids.clear()
                line_form.tax_ids.add(
                    self.env.ref(
                        f"account.{self.company.id}_account_tax_template_{tax_xmlid}"
                    )
                )
                line_form.deductible_percentage = deductible_percentage
        bill = bill_form.save()
        bill.action_post()
        return bill

    def _get_assets(self, move):
        return self.env["account.asset"].search([("code", "=", move.name)])

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

    def test_non_deductible_other_rate(self):
        """Any non deductible VAT of the chart, not only the 21 %, is added"""
        asset = self._post_bill([(200, "p_iva10_nd")])
        self.assertEqual(asset.purchase_value, 220)

    def test_deductible_and_non_deductible_lines(self):
        """The deductible VAT of a line doesn't change the value of its asset,
        nor the non deductible VAT of another line"""
        assets = self._post_bill([(100, "p_iva21_bc"), (200, "p_iva0_nd")])
        self.assertEqual(assets.mapped("purchase_value"), [100, 242])

    def test_group_of_taxes(self):
        """An import of goods with the group of taxes of the DUA"""
        asset = self._post_bill([(100, "p_iva21_ibc_group")])
        self.assertEqual(asset.purchase_value, 100)

    def test_refund_non_deductible(self):
        """A vendor credit note gives the value with its sign"""
        asset = self._post_bill([(100, "p_iva0_nd")], move_type="in_refund")
        self.assertEqual(asset.purchase_value, -121)

    def test_foreign_currency_non_deductible(self):
        """The value is in the currency of the company, rounded with it"""
        asset = self._post_bill([(10000, "p_iva0_nd")], currency=self.jpy)
        # 10000 / 150 = 66.67 plus 2100 / 150 = 14.00
        self.assertEqual(asset.purchase_value, 80.67)

    def test_deductible_percentage(self):
        """A car bought for 100 + 21 % of VAT, deductible at 50 % (art. 95.Tres
        LIVA): Odoo core books the private part of the line on its own lines, on
        the account of the line, which are not another asset. The non deductible
        VAT is part of the value of the asset."""
        bill = self._post_bill_form([(100, "p_iva21_bc", 0.5)])
        asset = self._get_assets(bill)
        self.assertEqual(asset.mapped("purchase_value"), [110.5])
        self.assertEqual(bill.invoice_line_ids.asset_id, asset)

    def test_deductible_percentage_refund(self):
        """The credit note of the bill gives the same value with its sign"""
        bill = self._post_bill_form([(100, "p_iva21_bc", 0.5)])
        reversal = (
            self.env["account.move.reversal"]
            .with_user(self.account_user)
            .with_context(active_model="account.move", active_ids=bill.ids)
            .create({"journal_id": bill.journal_id.id})
        )
        refund = self.env["account.move"].browse(reversal.refund_moves()["res_id"])
        refund.action_post()
        self.assertEqual(self._get_assets(refund).mapped("purchase_value"), [-110.5])

    def test_deductible_percentage_several_lines(self):
        """Each line gets the VAT of its own private part, not the one of another
        line with the same tax. With a non deductible tax, all its quota is in the
        value."""
        bill = self._post_bill_form(
            [(100, "p_iva21_bc", 0.5), (300, "p_iva21_bc", 1), (200, "p_iva0_nd", 0.5)]
        )
        self.assertEqual(
            sorted(self._get_assets(bill).mapped("purchase_value")), [110.5, 242, 300]
        )

    def test_deductible_percentage_no_vat_taxes(self):
        """Only the VAT of the private part is in the value: not the child that
        subtracts the base in the group of taxes of the DUA, nor a withholding"""
        bill = self._post_bill_form(
            [(100, "p_iva21_ibc_group", 0.5), (200, "p_irpf15", 0.5)]
        )
        self.assertEqual(
            sorted(self._get_assets(bill).mapped("purchase_value")), [110.5, 200]
        )
