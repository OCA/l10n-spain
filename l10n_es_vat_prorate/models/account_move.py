# Copyright 2021 Creu Blanca
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later(http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models
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

    def button_draft(self):
        res = super().button_draft()
        for move in self:
            move._apply_vat_prorate()
        return res

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
            prec = invoice_line.move_id.currency_id.rounding
            account_id = invoice_line.account_id.id
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
                if tax.id in taxes_with_prorate:
                    taxes_with_prorate[tax.id]["tax_total"] += float_round(
                        invoice_line.balance * tax.amount / 100, precision_rounding=prec
                    )
                else:
                    taxes_with_prorate.update(
                        {
                            tax.id: {
                                "tax_total": float_round(
                                    invoice_line.balance * tax.amount / 100,
                                    precision_rounding=prec,
                                )
                            }
                        }
                    )
        return taxes_with_prorate

    def _get_lines_with_tax_prorate(self):
        return self.line_ids.filtered_domain(
            [
                ("vat_prorate", "=", False),
                ("tax_line_id.with_vat_prorate", "=", True),
            ]
        )

    def _get_invoice_line_with_prorate(self):
        self.ensure_one()
        return self.invoice_line_ids.filtered_domain([("with_vat_prorate", "=", True)])

    def _apply_vat_prorate(self):
        """Recalculate move.line_ids by applying the prorate.
        If a move line with with_tax_prorate=True already has a prorate_line,
        we need to recalculate the prorate and tax.
        If a move line with with_tax_prorate=True does not have a
        prorate_line, we need to use the copy method to create a new line
        with the prorate applied and recalculate prorate balance and tax balance
        We group the prorate lines by Tax->Account->Analytic Distribution.
        """
        invoice_lines_with_prorate = self._get_invoice_line_with_prorate()
        taxes_with_prorate, prorate_vals = self._calculate_vat_prorate(
            invoice_lines_with_prorate
        )
        line_to_update = {"line_ids": []}
        tax_lines = self._get_lines_with_tax_prorate()
        prorate_lines = tax_lines.prorate_line_ids.filtered_domain(
            [("vat_prorate", "=", True)]
        )
        prorate_lines.with_context(
            dynamic_unlink=True
        ).unlink()  # Remove all prorate lines
        for tax_id, prorate_taxes in prorate_vals.items():
            prorate_amount = 0
            tax_line = tax_lines.filtered_domain(
                [("tax_line_id", "=", tax_id), ("account_type", "=", "asset_current")]
            )
            prorate_line_ids = []
            for prorate_data in prorate_taxes.values():
                prorate_line = tax_line.copy()
                tax_total = prorate_data.get("tax_total", 0)
                prorate_total = prorate_data.get("prorate_total", 0)
                prorate_amount += tax_total - prorate_total
                prorate_line_ids.append(prorate_line.id)
                line_to_update["line_ids"].append(
                    (
                        1,
                        prorate_line.id,
                        {
                            "balance": tax_total - prorate_total,
                            "account_id": prorate_data["account_id"],
                            "analytic_distribution": prorate_data[
                                "analytic_distribution"
                            ],
                            "vat_prorate": True,
                        },
                    )
                )
            tax_val = taxes_with_prorate.pop(tax_id)
            line_to_update["line_ids"].append(
                [
                    1,
                    tax_line.id,
                    {
                        "balance": tax_val["tax_total"] - prorate_amount,
                        "prorate_line_ids": [fields.Command.set(prorate_line_ids)],
                    },
                ]
            )
        for tax_id, tax_val in taxes_with_prorate.items():
            tax_line = tax_lines.filtered_domain([("tax_line_id", "=", tax_id)])
            line_to_update["line_ids"].append(
                [
                    1,
                    tax_line.id,
                    {
                        "balance": tax_val["tax_total"],
                    },
                ]
            )
        self.with_context(skip_vat_prorate=True).write(line_to_update)

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        for move in moves:
            if move.move_type in ["in_invoice", "in_refund"]:
                move._apply_vat_prorate()
        return moves

    def write(self, vals):
        res = super().write(vals)
        for move in self:
            if (
                move.move_type in ["in_invoice", "in_refund"]
                and not self.env.context.get("skip_vat_prorate", False)
                and move.state == "draft"
                and (
                    "line_ds" in vals
                    and len(vals["line_ids"])
                    or "invoice_line_ids" in vals
                )
                or any(
                    key in vals
                    for key in [
                        "partner_id",
                        "currency_id",
                        "invoice_currency_rate",
                        "prorate_id",
                        "date",
                        "invoice_date",
                    ]
                )
            ):
                move._apply_vat_prorate()
        return res


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
