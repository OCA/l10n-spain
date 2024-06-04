# Copyright 2021 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_round, frozendict


class AccountMove(models.Model):
    _inherit = "account.move"

    with_special_vat_prorate = fields.Boolean(
        related="company_id.with_special_vat_prorate"
    )


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_prorate = fields.Boolean(
        string="Is vat prorate", help="The line is a vat prorate"
    )

    with_vat_prorate = fields.Boolean(
        string="With Vat prorate",
        help="The line will create a vat prorate",
        default=lambda self: (
            self.env.company.with_vat_prorate
            and (
                not self.env.company.with_special_vat_prorate
                or self.env.company.with_special_vat_prorate_default
            )
        ),
    )

    def _process_aeat_tax_fee_info(self, res, tax, sign):
        result = super()._process_aeat_tax_fee_info(res, tax, sign)
        if self.vat_prorate:
            res[tax]["deductible_amount"] -= self.balance * sign
        return result

    @api.depends("with_vat_prorate")
    def _compute_all_tax(self):
        """After getting normal taxes dict that is dumped into this field, we loop
        into it to check if any of them applies VAT prorate, and if it's the case,
        we modify its amount and add the corresponding extra tax line.
        """
        res = None
        for line in self:
            res = super(AccountMoveLine, line)._compute_all_tax()
            prorate_tax_list = {}
            vat_prorate_date = line.date or line.invoice_date or fields.Date.today()
            for tax_key, tax_vals in line.compute_all_tax.items():
                tax_vals["vat_prorate"] = False
                tax = (
                    self.env["account.tax.repartition.line"]
                    .browse(tax_key.get("tax_repartition_line_id", False))
                    .tax_id
                )
                if (
                    line.with_vat_prorate
                    and tax.with_vat_prorate
                    and tax_key.get("account_id")
                    and (
                        not tax.prorate_account_ids
                        or tax_key.get("account_id") in tax.prorate_account_ids.ids
                    )
                ):
                    prec = line.move_id.currency_id.rounding
                    prorate = line.company_id.get_prorate(vat_prorate_date)
                    new_vals = tax_vals.copy()
                    for field in {"amount_currency", "balance"}:
                        tax_vals[field] = float_round(
                            tax_vals[field] * (prorate / 100),
                            precision_rounding=prec,
                        )
                        new_vals[field] -= tax_vals[field]
                    new_vals["vat_prorate"] = True
                    new_key = dict(tax_key)
                    new_key.update(
                        {
                            "vat_prorate": True,
                            "account_id": line.account_id.id,
                            "analytic_distribution": line.analytic_distribution,
                        }
                    )
                    new_key = frozendict(new_key)
                    if prorate_tax_list.get(new_key):
                        for field in {"amount_currency", "balance"}:
                            prorate_tax_list[new_key][field] += new_vals[field]
                    else:
                        prorate_tax_list[new_key] = new_vals
            if prorate_tax_list:
                line.compute_all_tax.update(prorate_tax_list)
        return res
