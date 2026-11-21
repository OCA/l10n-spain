# Copyright 2021 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later(http://www.gnu.org/licenses/agpl).


import json
from contextlib import contextmanager

from odoo import Command, api, fields, models
from odoo.tools import float_round


class AccountMove(models.Model):
    _inherit = "account.move"

    prorate_id = fields.Many2one(
        "res.company.vat.prorate",
        compute="_compute_prorate_id",
        store=True,
        copy=False,
    )
    with_special_vat_prorate = fields.Boolean(
        compute="_compute_prorate_id",
        store=True,
        copy=False,
    )

    @api.depends("company_id", "date", "invoice_date")
    def _compute_prorate_id(self):
        self.prorate_id = False
        self.with_special_vat_prorate = False
        for rec in self:
            if rec.company_id.with_vat_prorate:
                prorate_date = rec.date or rec.invoice_date or fields.Date.today()
                if rec.move_type == "in_refund":
                    prorate_date = (
                        rec.reversed_entry_id.date or rec.reversed_entry_id.invoice_date
                        if rec.reversed_entry_id
                        else prorate_date
                    )
                rec.prorate_id = rec.company_id.get_prorate(prorate_date)
                rec.with_special_vat_prorate = rec.prorate_id.type == "special"

    def _get_sync_stack(self, container):
        stack, update_containers = super()._get_sync_stack(container)
        invoice_container = update_containers()[1]
        # Exits after the tax lines (50) and the private part lines (60)
        stack.append((46, self._sync_vat_prorate_lines(invoice_container)))
        return stack, update_containers

    @contextmanager
    def _sync_vat_prorate_lines(self, container):
        """Apply the prorate each time Odoo core computes the tax lines again, as it
        does when the lines are written on their own (journal items list, imported
        documents) and not only through the bill."""
        yield
        for move in container["records"]:
            if move.state == "draft" and move.move_type in ("in_invoice", "in_refund"):
                move._apply_vat_prorate()

    def _calculate_vat_prorate(self, invoice_lines):
        """This method calculates tax_total and prorate_total for each line of
        the invoice that has taxes with with_vat_prorate set to True.
        In the case of special prorate, count all taxes
        with with_vat_prorate True and False from all invoice lines
        """
        taxes_with_prorate = {}
        prorate_vals = {}
        for invoice_line in invoice_lines:
            prorate = invoice_line.move_id.prorate_id.vat_prorate / 100.0
            prorate_account_id = invoice_line.move_id.prorate_id.account_id.id
            prec = invoice_line.move_id.currency_id.rounding
            account_id = prorate_account_id or invoice_line.account_id.id
            analytic_distribution = invoice_line.analytic_distribution
            # It's need to group by tax_id, analytic_distribution and account_id
            uniq_line_key = f"{analytic_distribution}|{account_id}"
            for tax in invoice_line.tax_ids.filtered(lambda t: t.with_vat_prorate):
                tax_total = float_round(
                    invoice_line.balance * tax.amount / 100, precision_rounding=prec
                )
                prorate_total = float_round(
                    tax_total * prorate, precision_rounding=prec
                )
                if tax.id in taxes_with_prorate:
                    taxes_with_prorate[tax.id]["tax_total"] += tax_total
                else:
                    taxes_with_prorate[tax.id] = {
                        "tax_total": tax_total,
                    }
                if tax.id in prorate_vals:
                    if uniq_line_key in prorate_vals[tax.id]:
                        prorate_vals[tax.id][uniq_line_key]["tax_total"] += tax_total
                        prorate_vals[tax.id][uniq_line_key]["prorate_total"] += (
                            prorate_total
                        )
                    else:
                        prorate_vals[tax.id].update(
                            {
                                uniq_line_key: {
                                    "tax_total": tax_total,
                                    "prorate_total": prorate_total,
                                    "account_id": account_id,
                                    "analytic_distribution": analytic_distribution,
                                }
                            }
                        )
                else:
                    prorate_vals.update(
                        {
                            tax.id: {
                                uniq_line_key: {
                                    "tax_total": tax_total,
                                    "prorate_total": prorate_total,
                                    "account_id": account_id,
                                    "analytic_distribution": analytic_distribution,
                                }
                            }
                        }
                    )
        if self.with_special_vat_prorate:
            taxes_with_prorate = self._calculate_all_tax_with_prorate(
                taxes_with_prorate
            )
        return (taxes_with_prorate, prorate_vals)

    def _calculate_all_tax_with_prorate(self, taxes_with_prorate):
        """
        In the case of special prorate, count all taxes on invoice lines
        with the with_vat_prorate False.
        It's need to recover the total tax and apply the prorate correctly.
        """
        self.ensure_one()
        for invoice_line in self.invoice_line_ids.filtered_domain(
            [("with_vat_prorate", "=", False)]
        ):
            prec = invoice_line.move_id.currency_id.rounding
            for tax in invoice_line.tax_ids.filtered(lambda t: t.with_vat_prorate):
                tax_total = float_round(
                    invoice_line.balance * tax.amount / 100, precision_rounding=prec
                )
                taxes_with_prorate.setdefault(tax.id, {"tax_total": 0})
                taxes_with_prorate[tax.id]["tax_total"] += tax_total
        return taxes_with_prorate

    def _get_invoice_line_with_prorate(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered_domain([("with_vat_prorate", "=", True)])

    def _get_vat_prorate_lines_key(self, vals_list):
        """Comparable values of the prorate lines of a tax."""
        return sorted(
            (
                vals["account_id"],
                json.dumps(vals["analytic_distribution"] or {}, sort_keys=True),
                self.company_currency_id.round(vals["balance"]),
            )
            for vals in vals_list
        )

    def _apply_vat_prorate(self):
        """Split the deductible quota of each prorated tax between its tax line and
        the prorate lines, grouped by account and analytic distribution.

        It runs after Odoo core computes the tax lines, which drops the prorate
        lines and gives the whole quota back to the tax line, or keeps them as they
        are, so the lines are written only when they differ from the expected ones.
        """
        self.ensure_one()
        prorate_lines = self.line_ids.filtered("vat_prorate")
        if not self.prorate_id and not prorate_lines:
            return
        taxes_with_prorate, prorate_vals = self._calculate_vat_prorate(
            self._get_invoice_line_with_prorate()
        )
        currency = self.company_currency_id
        taxes = (
            self.env["account.tax"].browse(list(taxes_with_prorate))
            | prorate_lines.tax_line_id
        )
        # The deductible side only: a self-assessed tax has its output VAT too
        tax_lines = self.line_ids.filtered(
            lambda line: (
                not line.vat_prorate
                and line.tax_line_id in taxes
                and line.account_type == "asset_current"
            )
        )
        for tax in taxes:
            tax_line = tax_lines.filtered(lambda line, tax=tax: line.tax_line_id == tax)
            if not tax_line:
                # No quota (lines without amount): Odoo core makes no tax line
                continue
            old_prorate_lines = prorate_lines.filtered(
                lambda line, tax=tax: line.tax_line_id == tax
            )
            new_vals = []
            for data in prorate_vals.get(tax.id, {}).values():
                balance = currency.round(data["tax_total"] - data["prorate_total"])
                if not currency.is_zero(balance):
                    new_vals.append(
                        {
                            "account_id": data["account_id"],
                            "analytic_distribution": data["analytic_distribution"],
                            "balance": balance,
                        }
                    )
            if tax.id in taxes_with_prorate:
                tax_balance = taxes_with_prorate[tax.id]["tax_total"] - sum(
                    vals["balance"] for vals in new_vals
                )
            else:
                # Prorate no longer applied: the tax line takes its quota back
                tax_balance = tax_line.balance + sum(
                    old_prorate_lines.mapped("balance")
                )
            old_vals = [
                {
                    "account_id": line.account_id.id,
                    "analytic_distribution": line.analytic_distribution,
                    "balance": line.balance,
                }
                for line in old_prorate_lines
            ]
            old_key = self._get_vat_prorate_lines_key(old_vals)
            if old_key == self._get_vat_prorate_lines_key(new_vals) and not (
                currency.compare_amounts(tax_line.balance, tax_balance)
            ):
                continue
            old_prorate_lines.with_context(dynamic_unlink=True).unlink()
            new_prorate_lines = self.env["account.move.line"]
            for vals in new_vals:
                new_prorate_line = tax_line.copy({"account_id": vals["account_id"]})
                # Not the account again: it would give its default taxes to the line
                new_prorate_line.write(
                    {
                        "balance": vals["balance"],
                        "analytic_distribution": vals["analytic_distribution"],
                        "vat_prorate": True,
                    }
                )
                new_prorate_lines |= new_prorate_line
            tax_line.write(
                {
                    "balance": tax_balance,
                    "prorate_line_ids": [Command.set(new_prorate_lines.ids)],
                }
            )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_prorate = fields.Boolean(
        string="Is vat prorate",
        help="The line is a vat prorate",
        copy=False,
    )

    with_vat_prorate = fields.Boolean(
        compute="_compute_with_vat_prorate",
        store=True,
        readonly=False,
        copy=False,
    )

    prorate_line_ids = fields.Many2many(
        "account.move.line",
        relation="account_move_line_prorate_move_line_rel",
        column1="account_move_line_id",
        column2="prorate_move_line_id",
        copy=False,
    )

    @api.depends("move_id.prorate_id", "company_id")
    def _compute_with_vat_prorate(self):
        for rec in self:
            rec.with_vat_prorate = rec.move_id.company_id.with_vat_prorate and (
                rec.move_id.prorate_id.type == "general"
                or rec.move_id.prorate_id.special_vat_prorate_default
            )

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        result = super()._process_aeat_tax_fee_info(res, tax, sign)
        if self.vat_prorate:
            res[tax]["deductible_amount"] -= self.balance * sign
        return result
