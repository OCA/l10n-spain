# Copyright 2021 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later[](http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    prorate_id = fields.Many2one(
        "res.company.vat.prorate",
        compute="_compute_prorate_id",
        store=True,
    )
    with_special_vat_prorate = fields.Boolean(
        compute="_compute_prorate_id",
        store=True,
    )

    @api.depends("company_id", "date", "invoice_date")
    def _compute_prorate_id(self):
        for rec in self:
            if rec.company_id.with_vat_prorate:
                prorate_date = rec.date or rec.invoice_date or fields.Date.today()
                rec.prorate_id = rec.company_id.get_prorate(prorate_date)
                rec.with_special_vat_prorate = rec.prorate_id.type == "special"
            else:
                rec.prorate_id = rec.with_special_vat_prorate = False

    def button_draft(self):
        res = super().button_draft()
        for move in self:
            move._compute_prorate_id()
        return res

    def _apply_vat_prorate(self):
        if self.env.context.get("skip_vat_prorate"):
            return
        for move in self:
            if (
                move.reversed_entry_id
                or not move.is_invoice(include_receipts=True)
                or not move.is_purchase_document()
            ):
                continue

            ctx = dict(self.env.context, skip_vat_prorate=True)
            existing_prorate_lines = move.line_ids.filtered(
                lambda line: line.vat_prorate
            )

            if not move.prorate_id:
                for line in existing_prorate_lines:
                    if line.balance != 0.0:
                        line.write({"balance": 0.0, "amount_currency": 0.0})
                continue

            prorate = move.prorate_id.vat_prorate / 100.0
            currency = move.currency_id
            expense_account = move._get_prorate_expense_account()

            for tax_line in move.line_ids.filtered(
                lambda aml: aml.tax_line_id and not aml.vat_prorate
            ):
                if tax_line.original_balance:
                    base_balance = tax_line.original_balance
                    base_currency = tax_line.original_amount_currency
                else:
                    base_balance = tax_line.balance
                    base_currency = tax_line.amount_currency
                    tax_line.write(
                        {
                            "original_balance": base_balance,
                            "original_amount_currency": base_currency,
                        }
                    )

                deductible_balance = float_round(
                    base_balance * prorate, precision_rounding=currency.rounding
                )
                deductible_currency = float_round(
                    base_currency * prorate, precision_rounding=currency.rounding
                )
                non_deductible_balance = base_balance - deductible_balance
                non_deductible_currency = base_currency - deductible_currency

                tax_line.write(
                    {
                        "balance": deductible_balance,
                        "amount_currency": deductible_currency,
                    }
                )

                if not currency.is_zero(non_deductible_balance):
                    prorate_line = existing_prorate_lines.filtered(
                        lambda pl, tax_line=tax_line: pl.tax_line_id
                        == tax_line.tax_line_id
                    )
                    if prorate_line:
                        prorate_line = prorate_line[0].with_context(**ctx)
                        prorate_line.write(
                            {
                                "balance": non_deductible_balance,
                                "amount_currency": non_deductible_currency,
                                "account_id": expense_account.id,
                                "partner_id": move.partner_id.id,
                            }
                        )
                    else:
                        tax_line.with_context(**ctx).copy(
                            default={
                                "move_id": move.id,
                                "balance": non_deductible_balance,
                                "amount_currency": non_deductible_currency,
                                "account_id": expense_account.id,
                                "partner_id": move.partner_id.id,
                                "vat_prorate": True,
                                "display_type": "tax",
                            }
                        )

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if (
                not move.reversed_entry_id
                and move.is_invoice(include_receipts=True)
                and move.is_purchase_document()
                and not self.env.context.get("skip_vat_prorate")
            ):
                move._apply_vat_prorate()
        return moves

    def write(self, vals):
        res = super().write(vals)

        if self.env.context.get("skip_vat_prorate"):
            return res

        draft_moves = self.filtered(lambda m: m.state == "draft")
        if not draft_moves:
            return res

        relevant_fields = {
            "line_ids",
            "invoice_line_ids",
            "prorate_id",
            "date",
            "invoice_date",
        }
        if relevant_fields.intersection(vals.keys()):
            for move in draft_moves:
                if (
                    move.is_invoice(include_receipts=True)
                    and move.is_purchase_document()
                ):
                    move._apply_vat_prorate()

        return res

    def _get_prorate_expense_account(self):
        for line in self.line_ids:
            if line.debit > 0 and not line.tax_line_id:
                if line.account_id.account_type not in (
                    "asset_receivable",
                    "liability_payable",
                ):
                    return line.account_id
        return self.company_id.expense_currency_exchange_account_id


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_prorate = fields.Boolean(
        string="VAT Prorate",
        help="This line represents the non-deductible part of the prorated VAT.",
    )

    with_vat_prorate = fields.Boolean(
        compute="_compute_with_vat_prorate",
        store=True,
        readonly=False,
    )

    is_zero_line = fields.Boolean(
        compute="_compute_is_zero_line",
        store=True,
        help="True when both debit and credit are zero",
    )

    original_balance = fields.Monetary(
        copy=False,
        help=(
            "Original balance before applying VAT prorate,"
            " used to prevent cumulative recalculations."
        ),
    )

    original_amount_currency = fields.Monetary(
        copy=False,
        help=(
            "Original amount in transaction currency before VAT prorate recalculation."
        ),
    )

    @api.depends("debit", "credit")
    def _compute_is_zero_line(self):
        for line in self:
            line.is_zero_line = line.debit == 0.0 and line.credit == 0.0

    @api.depends("move_id.prorate_id", "move_id.company_id.with_vat_prorate")
    def _compute_with_vat_prorate(self):
        for line in self:
            prorate = line.move_id.prorate_id
            if not line.move_id.company_id.with_vat_prorate or not prorate:
                line.with_vat_prorate = False
            elif prorate.type == "general":
                line.with_vat_prorate = True
            elif prorate.type == "special":
                line.with_vat_prorate = prorate.special_vat_prorate_default
            else:
                line.with_vat_prorate = False

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        result = super()._process_aeat_tax_fee_info(res, tax, sign)
        if self.vat_prorate:
            res[tax]["deductible_amount"] -= self.balance * sign
        return result
