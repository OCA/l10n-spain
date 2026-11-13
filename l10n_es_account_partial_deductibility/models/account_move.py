# Copyright 2026 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from collections import defaultdict
from contextlib import contextmanager

from odoo import models
from odoo.fields import Command


class AccountMove(models.Model):
    _inherit = "account.move"

    def _get_sync_stack(self, container):
        stack, update_containers = super()._get_sync_stack(container)
        invoice_container = update_containers()[1]
        # Exits after the private part lines (60) and the tax lines (50)
        stack.append((45, self._sync_private_part_line_accounts(invoice_container)))
        return stack, update_containers

    @contextmanager
    def _sync_private_part_line_accounts(self, container):
        """Keep the private part of a partially deductible vendor bill line
        (``deductible_percentage``, art. 95 LIVA) on the account of the line.

        Odoo core books the private base and VAT on the Private Share Account
        of the purchase journal (544 in the Spanish chart) or, without one, on
        its default account. In Spain the non deductible VAT is part of the
        cost of the asset or expense (PGC, norma de registro y valoración 12ª),
        whatever that account, so each line account
        gets back its private base plus its private VAT on its own total line.
        The single private tax line goes to the account of the first line, and
        the total line of that account gives back the private VAT of the other
        accounts, so the untaxed and tax amounts of the bill are unchanged.
        """
        yield
        for move in container["records"]:
            if move.state == "draft" and move.country_code == "ES":
                move._set_private_part_line_accounts()

    def _set_private_part_line_accounts(self):
        private_lines = self.line_ids.filtered(
            lambda line: line.display_type == "non_deductible_product"
        ).sorted("sequence")
        if not private_lines:
            return
        # Private base and VAT of each account, in company and bill currency
        amounts = defaultdict(lambda: [0.0, 0.0])
        for line in private_lines:
            amounts[line.account_id][0] -= line.balance
            amounts[line.account_id][1] -= line.amount_currency
        private_vat = [0.0, 0.0]
        for base_line in self._get_rounded_base_and_tax_lines()[0]:
            line = base_line["record"]
            if not line or line not in private_lines:
                continue
            details = base_line["tax_details"]
            for i, suffix in enumerate(("", "_currency")):
                # As Odoo core computes the amount of the private tax line
                vat = -base_line["sign"] * (
                    details[f"total_included{suffix}"]
                    - details[f"total_excluded{suffix}"]
                )
                amounts[line.account_id][i] += vat
                private_vat[i] += vat
        main_account = private_lines[0].account_id
        amounts[main_account][0] -= private_vat[0]
        amounts[main_account][1] -= private_vat[1]
        total_lines = self.line_ids.filtered(
            lambda line: line.display_type == "non_deductible_product_total"
        )
        vals_list = [
            {
                "account_id": account.id,
                "balance": self.company_currency_id.round(balance),
                "amount_currency": self.currency_id.round(amount_currency),
                # A new account would give its taxes to the line
                "tax_ids": [Command.clear()],
            }
            for account, (balance, amount_currency) in amounts.items()
        ]
        for line, vals in zip(total_lines, vals_list, strict=False):
            line.write(vals)
        self.env["account.move.line"].create(
            [
                {
                    **vals,
                    "move_id": self.id,
                    "display_type": "non_deductible_product_total",
                    "name": total_lines[:1].name,
                    "sequence": total_lines[:1].sequence,
                }
                for vals in vals_list[len(total_lines) :]
            ]
        )
        total_lines[len(vals_list) :].with_context(dynamic_unlink=True).unlink()
        self.line_ids.filtered(
            lambda line: line.display_type == "non_deductible_tax"
        ).write({"account_id": main_account.id, "tax_ids": [Command.clear()]})
