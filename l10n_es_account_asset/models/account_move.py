# Copyright 2025 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import float_compare

# Lines where Odoo core books the private part of a vendor bill line with a
# deductible percentage (art. 95.Tres LIVA)
PRIVATE_PART_DISPLAY_TYPES = (
    "non_deductible_product",
    "non_deductible_product_total",
    "non_deductible_tax",
)
# Taxes that are not VAT, whose quota of the private part is not part of the
# value of the asset: withholdings and the child of the group of taxes of the DUA
# that subtracts the base
NO_VAT_TAX_TYPES = ("ignore", "retencion")


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_asset_tax_info(self):
        """Base, quota and deductible quota of each tax, as ``_get_aeat_tax_info``
        gets them from the base and tax lines, without the private part of the
        lines with a deductible percentage, whose quota is taken apart.

        Odoo core books that private part on its own lines: a negative base on
        the account of the line, which counts here, so the base is the deductible
        part, and the quota of that part, which doesn't (it takes the taxes of its
        account). The result doesn't depend on how ``_get_aeat_tax_info`` handles
        those lines.
        """
        self.ensure_one()
        res = {}
        sign = -1 if self.move_type[:3] == "out" else 1
        for line in self.line_ids:
            if line.display_type == "non_deductible_tax":
                continue
            for tax in line.tax_ids:
                line._process_aeat_tax_base_info(res, tax, sign)
            tax = line.tax_line_id
            if not tax:
                continue
            if "invoice" in self.move_type:
                repartition_lines = tax.invoice_repartition_line_ids
            else:
                repartition_lines = tax.refund_repartition_line_ids
            if (
                len(repartition_lines) > 2
                and line.tax_repartition_line_id.factor_percent < 0
            ):
                # taxes with more than one "tax" repartition line must be discarded
                continue
            line._process_aeat_tax_fee_info(res, tax, sign)
        return res

    def _get_asset_private_tax_info(self):
        """Private base and its quota of each VAT tax, from the lines with a
        deductible percentage, the quota as Odoo core computes the line where it
        books it."""
        self.ensure_one()
        res = {}
        lines = self.line_ids.filtered(lambda line: line.display_type == "product")
        for line in lines:
            private_base = line._get_asset_private_base()
            if not private_base:
                continue
            for tax in line.tax_ids.flatten_taxes_hierarchy():
                if tax.l10n_es_type in NO_VAT_TAX_TYPES:
                    continue
                res.setdefault(tax, {"base": 0, "amount": 0})
                res[tax]["base"] += private_base
        if not res:
            return res
        for base_line in self._get_rounded_base_and_tax_lines()[0]:
            if base_line["special_type"] != "non_deductible":
                continue
            for tax_data in base_line["tax_details"]["taxes_data"]:
                if tax_data["tax"] in res:
                    res[tax_data["tax"]]["amount"] -= (
                        base_line["sign"] * tax_data["tax_amount"]
                    )
        return res

    def _prepare_asset_vals(self, aml):
        """The non deductible tax of the line is part of the purchase value of the
        asset (PGC, norma de registro y valoración 2ª, 1.1 and 12ª): the one of a
        non deductible tax, of a prorate, and of the private part of a line with a
        deductible percentage. The base of the line is the purchase value
        excluding tax, also its private part."""
        res = super()._prepare_asset_vals(aml)
        # As we only know the deductible amount at invoice level, we get the
        # general tax info, and then apply the percentage corresponding to the
        # deductible base of this line
        main_vals = self._get_asset_tax_info()
        private_vals = self._get_asset_private_tax_info()
        private_base = aml._get_asset_private_base()
        amount = aml.balance
        # The tax info is given by child tax for a group of taxes
        for tax in aml.tax_ids.flatten_taxes_hierarchy():
            tax_vals = main_vals[tax]
            if tax_vals["amount"] != tax_vals["deductible_amount"]:
                ratio = (aml.balance - private_base) / tax_vals["base"]
                diff = tax_vals["amount"] - tax_vals["deductible_amount"]
                amount += diff * ratio
            if private_base and tax in private_vals:
                ratio = private_base / private_vals[tax]["base"]
                amount += private_vals[tax]["amount"] * ratio
        res["purchase_value"] = aml.company_currency_id.round(amount)
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    @api.depends("display_type")
    def _compute_asset_profile(self):
        """The private part of a line with a deductible percentage is in the
        purchase value of the asset of that line, its lines are not an asset,
        even if they are on an asset account."""
        private_lines = self.filtered(
            lambda line: line.display_type in PRIVATE_PART_DISPLAY_TYPES
        )
        private_lines.asset_profile_id = False
        return super(AccountMoveLine, self - private_lines)._compute_asset_profile()

    def _get_asset_private_base(self):
        """Private part of the balance of a line with a deductible percentage,
        rounded as Odoo core does for the line where it takes it out."""
        self.ensure_one()
        if not float_compare(self.deductible_percentage, 1, precision_digits=4):
            return 0.0
        return self.company_currency_id.round(
            self.balance * (1 - self.deductible_percentage)
        )
