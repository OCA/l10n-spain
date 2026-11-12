# Copyright 2022 CreuBlanca
# Copyright 2022 Tecnativa - Víctor Martínez
# Copyright 2022 NuoBiT - Eric Antones
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    thirdparty_invoice = fields.Boolean(
        string="Third-party invoice",
        copy=False,
        compute="_compute_thirdparty_invoice",
        store=True,
        readonly=False,
    )
    thirdparty_number = fields.Char(
        string="Third-party number",
        index=True,
        copy=False,
        help="Número de la factura emitida por un tercero.",
    )

    @api.depends("journal_id")
    def _compute_thirdparty_invoice(self):
        for item in self:
            item.thirdparty_invoice = item.journal_id.thirdparty_invoice

    def _get_aeat_tax_info(self):
        """Base, quota and deductible quota of each tax of the invoice.

        Base and quota are the ones of the invoice as issued. Odoo core takes
        the non deductible part of a vendor bill line (``deductible_percentage``,
        arts. 95 and 96 LIVA) out of the base and the tax lines into its own
        lines: that part of the quota counts in the quota, not in the deductible
        quota.
        """
        self.ensure_one()
        res = {}
        sign = -1 if self.move_type[:3] == "out" else 1
        for line in self.line_ids:
            if line.display_type in ("non_deductible_product", "non_deductible_tax"):
                # The private part, added below to the quota of each tax. The
                # private quota line gets the taxes of its account.
                continue
            for tax in line.tax_ids:
                line._process_aeat_tax_base_info(res, tax, sign)
            if line.tax_line_id:
                tax = line.tax_line_id
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
        self._process_aeat_non_deductible_tax_info(res, sign)
        return res

    def _process_aeat_non_deductible_tax_info(self, res, sign):
        """Add to the quota of each tax its non deductible part, which Odoo core
        books on a single line for all the taxes, computed per tax as Odoo core
        computes that line."""
        if "non_deductible_product" not in self.line_ids.mapped("display_type"):
            return
        base_lines = self._get_rounded_base_and_tax_lines()[0]
        for base_line in base_lines:
            if base_line["special_type"] != "non_deductible":
                continue
            for tax_data in base_line["tax_details"]["taxes_data"]:
                tax = tax_data["tax"]
                res.setdefault(
                    tax, {"tax": tax, "base": 0, "amount": 0, "deductible_amount": 0}
                )
                res[tax]["amount"] -= base_line["sign"] * tax_data["tax_amount"] * sign


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    l10n_es_aeat_real_estate_id = fields.Many2one(
        comodel_name="l10n.es.aeat.real_estate",
        string="Real Estate",
        help="Real Estate related to this move line",
        # The landlord of a received invoice or the company leasing its premises
        domain="[('company_id', '=', company_id), '|', "
        "('partner_id', '=', partner_id), ('owned_by_company', '=', True)]",
    )

    def _process_aeat_tax_base_info(self, res, tax, sign):
        """It modifies the dictionary given in res for setting the base amount info
        for the taxes dictionary obtained in ~~account.move~~._get_aeat_tax_info().
        """
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        for child_tax in taxes:
            res.setdefault(
                child_tax,
                {"tax": child_tax, "base": 0, "amount": 0, "deductible_amount": 0},
            )
            res[child_tax]["base"] += self.balance * sign

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        """It modifies the dictionary given in res for setting the tax amount info
        for the taxes dictionary obtained in ~~account.move~~._get_aeat_tax_info().
        """
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        for child_tax in taxes:
            res.setdefault(
                child_tax,
                {"tax": child_tax, "base": 0, "amount": 0, "deductible_amount": 0},
            )
            amount = self.balance * sign
            res[child_tax]["amount"] += amount
            # Don't add it here if non deductible
            group = child_tax.tax_group_id
            if not group.get_external_id()[group.id].endswith("_tax_group_iva_nd"):
                res[child_tax]["deductible_amount"] += amount
