# Copyright 2021 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import float_round, frozendict


class AccountMove(models.Model):
    _inherit = "account.move"

    prorate_id = fields.Many2one(
        string="Prorate",
        comodel_name="res.company.vat.prorate",
        compute="_compute_prorate_id",
        ondelete="restrict",
        store=True,
    )
    with_special_vat_prorate = fields.Boolean(compute="_compute_prorate_id", store=True)

    @api.depends("company_id", "date", "invoice_date")
    def _compute_prorate_id(self):
        for rec in self:
            if rec.company_id.with_vat_prorate:
                prorate_date = rec.date or rec.invoice_date or fields.Date.today()
                rec.prorate_id = rec.company_id.get_prorate(prorate_date)
                rec.with_special_vat_prorate = rec.prorate_id.type == "special"
            else:
                rec.prorate_id = rec.with_special_vat_prorate = False


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    vat_prorate = fields.Boolean(
        string="Is vat prorate", help="The line is a vat prorate"
    )

    with_vat_prorate = fields.Boolean(
        string="With VAT Prorate",
        help="The line will create a vat prorate",
        compute="_compute_with_vat_prorate",
        store=True,
        readonly=False,
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
                    prorate = line.move_id.prorate_id.vat_prorate
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
