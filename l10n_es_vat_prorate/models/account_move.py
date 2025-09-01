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
        for move in self:
            existing_prorate_lines = move.line_ids.filtered(
                lambda line: line.vat_prorate
            )
            prorate_line_index = 0

            if not move.is_invoice(include_receipts=True):
                continue
            if not move.is_purchase_document():
                continue

            if not move.prorate_id:
                for line in existing_prorate_lines:
                    line.write(
                        {
                            "balance": 0.0,
                            "amount_currency": 0.0,
                        }
                    )
                continue

            prorate = move.prorate_id.vat_prorate / 100.0
            currency = move.currency_id

            for line in move.line_ids.filtered(
                lambda line: line.tax_line_id and not line.vat_prorate
            ):
                base_balance = line.balance
                base_currency = line.amount_currency

                deductible_balance = float_round(
                    base_balance * prorate, precision_rounding=currency.rounding
                )
                deductible_currency = float_round(
                    base_currency * prorate, precision_rounding=currency.rounding
                )

                non_deductible_balance = base_balance - deductible_balance
                non_deductible_currency = base_currency - deductible_currency

                line.balance = deductible_balance
                line.amount_currency = deductible_currency

                if not currency.is_zero(non_deductible_balance):
                    expense_account = move._get_prorate_expense_account()

                    if prorate_line_index < len(existing_prorate_lines):
                        prorate_line = existing_prorate_lines[prorate_line_index]
                        prorate_line.write(
                            {
                                "account_id": expense_account.id,
                                "balance": non_deductible_balance,
                                "amount_currency": non_deductible_currency,
                                "currency_id": line.currency_id.id
                                if line.currency_id
                                else None,
                                "partner_id": move.partner_id.id,
                            }
                        )
                        prorate_line_index += 1
                    else:
                        new_line = move.env["account.move.line"].create(
                            {
                                "move_id": move.id,
                                "account_id": expense_account.id,
                                "balance": non_deductible_balance,
                                "amount_currency": non_deductible_currency,
                                "currency_id": line.currency_id.id
                                if line.currency_id
                                else None,
                                "partner_id": move.partner_id.id,
                                "vat_prorate": True,
                                "display_type": "tax",
                            }
                        )
                        existing_prorate_lines |= new_line
                        prorate_line_index += 1
                elif prorate_line_index < len(existing_prorate_lines):
                    prorate_line = existing_prorate_lines[prorate_line_index]
                    prorate_line.write(
                        {
                            "balance": 0.0,
                            "amount_currency": 0.0,
                        }
                    )
                    prorate_line_index += 1

            for line in existing_prorate_lines[prorate_line_index:]:
                line.write(
                    {
                        "balance": 0.0,
                        "amount_currency": 0.0,
                    }
                )

    @api.depends(
        "invoice_line_ids.currency_rate",
        "invoice_line_ids.tax_base_amount",
        "invoice_line_ids.tax_line_id",
        "invoice_line_ids.price_total",
        "invoice_line_ids.price_subtotal",
        "invoice_payment_term_id",
        "partner_id",
        "currency_id",
    )
    def _compute_tax_totals(self):
        for move in self:
            super()._compute_tax_totals()
            if move.prorate_id and move.tax_totals:
                non_deductible_total = sum(
                    line.balance for line in move.line_ids.filtered("vat_prorate")
                )
                non_deductible_total_currency = sum(
                    line.amount_currency
                    for line in move.line_ids.filtered("vat_prorate")
                )
                move.tax_totals["total_amount"] += non_deductible_total
                move.tax_totals["total_amount_currency"] += (
                    non_deductible_total_currency
                )

                for subtotal in move.tax_totals.get("subtotals", []):
                    for tax_group in subtotal.get("tax_groups", []):
                        tax_group["tax_amount"] += non_deductible_total
                        tax_group["tax_amount_currency"] += (
                            non_deductible_total_currency
                        )
                        tax_group["display_base_amount"] += non_deductible_total
                        tax_group["display_base_amount_currency"] += (
                            non_deductible_total_currency
                        )
        return None

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._apply_vat_prorate()
        return moves

    def write(self, vals):
        if (
            any(key in vals for key in ["line_ids", "invoice_line_ids"])
            and self.state == "draft"
            and "state" not in vals
        ):
            res = super().write(vals)
            self._apply_vat_prorate()
        else:
            res = super().write(vals)
            if (
                any(key in vals for key in ["prorate_id", "date", "invoice_date"])
                and self.state == "draft"
                and "state" not in vals
            ):
                self._apply_vat_prorate()
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
        """Corrects SII submission: amount = full VAT, deductible_amount = prorated"""
        taxes = tax.amount_type == "group" and tax.children_tax_ids or tax
        prorate = 1.0
        if self.move_id.prorate_id and self.move_id.company_id.with_vat_prorate:
            prorate = self.move_id.prorate_id.vat_prorate / 100.0

        for t in taxes:
            res.setdefault(
                t, {"tax": t, "base": 0.0, "amount": 0.0, "deductible_amount": 0.0}
            )
            full_amount = abs(self.tax_base_amount * t.amount / 100.0 * sign)
            res[t]["amount"] += full_amount
            res[t]["deductible_amount"] += float_round(
                full_amount * prorate,
                precision_rounding=self.move_id.currency_id.rounding,
            )
        return res
