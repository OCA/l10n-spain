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
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        help="Número de la factura emitida por un tercero.",
    )

    @api.depends("journal_id")
    def _compute_thirdparty_invoice(self):
        for item in self:
            item.thirdparty_invoice = item.journal_id.thirdparty_invoice

    def _get_aeat_tax_info(self):
        self.ensure_one()
        res = {}
        sign = -1 if self.move_type[:3] == "out" else 1
        for line in self.line_ids:
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
        return res

    def _get_tax_info(self):
        """Deprecated, to be removed in migration"""
        _logger.warning(
            "Call to deprecated method '_get_tax_info', "
            "please use '_get_aeat_tax_info' instead"
        )
        return self._get_aeat_tax_info()


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    def _process_aeat_tax_base_info(self, res, tax, sign):
        """It modifies the dictionary given in res for setting the base amount info
        for the taxes dictionary obtained in ~~account.move~~._get_aeat_tax_info().
        """
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        for tax in taxes:
            res.setdefault(
                tax, {"tax": tax, "base": 0, "amount": 0, "deductible_amount": 0}
            )
            res[tax]["base"] += self.balance * sign

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        """It modifies the dictionary given in res for setting the tax amount info
        for the taxes dictionary obtained in ~~account.move~~._get_aeat_tax_info().
        """
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        for tax in taxes:
            res.setdefault(
                tax, {"tax": tax, "base": 0, "amount": 0, "deductible_amount": 0}
            )
            amount = self.balance * sign
            res[tax]["amount"] += amount
            res[tax]["deductible_amount"] += amount
