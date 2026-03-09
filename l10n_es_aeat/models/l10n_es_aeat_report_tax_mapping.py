# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016,2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, exceptions, fields, models
from odoo.fields import Domain


class L10nEsAeatReportTaxMapping(models.AbstractModel):
    _name = "l10n.es.aeat.report.tax.mapping"
    _inherit = "l10n.es.aeat.report"
    _description = (
        "Inheritable abstract model to add taxes by code mapping in any AEAT report"
    )

    tax_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.tax.line",
        inverse_name="res_id",
        domain=lambda self: [Domain("model", "=", self._name)],
        bypass_search_access=True,
        readonly=True,
        string="Tax lines",
    )
    valued_tax_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.tax.line",
        inverse_name="res_id",
        domain=lambda self: Domain.AND(
            [
                Domain("model", "=", self._name),
                Domain("amount", "!=", 0),
            ]
        ),
        bypass_search_access=True,
        readonly=True,
        string="Valued tax lines",
    )

    def calculate(self):
        res = super().calculate()
        for report in self:
            report.tax_line_ids.unlink()
            report.env.invalidate_all()
            # Buscar configuración de mapeo de impuestos
            domain_model = Domain("model", "=", report.number)
            domain_dt_from = Domain.OR(
                [
                    Domain("date_from", "<=", report.date_start),
                    Domain("date_from", "=", False),
                ]
            )
            domain_dt_to = Domain.OR(
                [
                    Domain("date_to", ">=", report.date_end),
                    Domain("date_to", "=", False),
                ]
            )
            tax_code_map = (
                self.env["l10n.es.aeat.map.tax"]
                .sudo()
                .with_context(active_test=False)
                .search(
                    Domain.AND([domain_model, domain_dt_from, domain_dt_to]),
                    limit=1,
                )
            )
            if tax_code_map:
                tax_lines = []
                for map_line in tax_code_map.map_line_ids:
                    tax_lines.append(report._prepare_tax_line_vals(map_line))
                report.tax_line_ids = [(0, 0, x) for x in tax_lines]
        return res

    def unlink(self):
        self.mapped("tax_line_ids").unlink()
        return super().unlink()

    def _prepare_tax_line_vals(self, map_line):
        self.ensure_one()
        move_lines = self._get_tax_lines(self.date_start, self.date_end, map_line)
        amount = map_line._get_amount_from_moves(move_lines)
        return {
            "model": self._name,
            "res_id": self.id,
            "map_line_id": map_line.id,
            "amount": amount,
            "move_line_ids": [(6, 0, move_lines.ids)],
        }

    def _get_partner_domain(self):
        return Domain([])

    def _get_move_line_domain(self, date_start, date_end, map_line):
        self.ensure_one()
        taxes = map_line.get_taxes_for_company(self.company_id)
        move_line_domain = Domain.AND(
            [
                Domain("company_id", "child_of", self.company_id.id),
                Domain("date", ">=", date_start),
                Domain("date", "<=", date_end),
                Domain("parent_state", "=", "posted"),
            ]
        )
        if map_line.move_type == "regular":
            move_line_domain &= Domain(
                "move_id.financial_type",
                "in",
                ["receivable", "payable", "liquidity", "other"],
            )
        elif map_line.move_type == "refund":
            move_line_domain &= Domain(
                "move_id.financial_type",
                "in",
                ["receivable_refund", "payable_refund"],
            )
        if map_line.field_type == "base":
            move_line_domain &= Domain("tax_ids", "in", taxes.ids)
        elif map_line.field_type == "amount":
            move_line_domain &= Domain("tax_line_id", "in", taxes.ids)
        else:  # map_line.field_type == 'both'
            move_line_domain &= Domain.OR(
                [
                    ("tax_line_id", "in", taxes.ids),
                    ("tax_ids", "in", taxes.ids),
                ]
            )
        if map_line.account_xmlid_ids:
            accounts = map_line.get_accounts_for_company(self.company_id)
            move_line_domain &= Domain("account_id", "in", accounts.ids)
        if map_line.sum_type == "debit":
            move_line_domain &= Domain("debit", ">", 0)
        elif map_line.sum_type == "credit":
            move_line_domain &= Domain("credit", ">", 0)
        if map_line.exigible_type == "yes":
            move_line_domain &= Domain.OR(
                [
                    Domain("move_id.tax_cash_basis_rec_id", "!=", False),
                    Domain("tax_line_id.tax_exigibility", "!=", "on_payment"),
                    Domain("tax_ids.tax_exigibility", "!=", "on_payment"),
                ]
            )
        elif map_line.exigible_type == "no":
            move_line_domain &= Domain.AND(
                [
                    Domain("move_id.tax_cash_basis_rec_id", "=", False),
                    Domain("tax_line_id.tax_exigibility", "=", "on_payment"),
                    Domain("tax_ids.tax_exigibility", "=", "on_payment"),
                ]
            )
        move_line_domain += self._get_partner_domain()
        return move_line_domain

    def _get_tax_lines(self, date_start, date_end, map_line):
        """Get the move lines for the codes and periods associated

        :param date_start: Start date of the period
        :param date_end: Stop date of the period
        :param map_line: Mapping line record
        :return: Move lines recordset that matches the criteria.
        """
        domain = self._get_move_line_domain(date_start, date_end, map_line)
        return self.env["account.move.line"].search(domain)

    @api.model
    def _prepare_regularization_move_line(self, **kwargs):
        return {
            "name": kwargs["account"].name,
            "account_id": kwargs["account"].id,
            "debit": kwargs["credit"],
            "credit": kwargs["debit"],
        }

    def _process_tax_line_regularization(self, tax_lines):
        self.ensure_one()
        groups = self.env["account.move.line"]._read_group(
            domain=Domain.AND(
                [
                    Domain("id", "in", tax_lines.move_line_ids.ids),
                    Domain("parent_state", "=", "posted"),
                ]
            ),
            groupby=["account_id"],
            aggregates=["debit:sum", "credit:sum"],
        )
        lines = []
        for group in groups:
            balance = group[1] - group[2]
            if balance:
                debit = balance if balance > 0 else 0
                credit = -balance if balance < 0 else 0
                lines.append(
                    self._prepare_regularization_move_line(
                        account=group[0], debit=debit, credit=credit
                    )
                )
        return lines

    @api.model
    def _prepare_counterpart_move_line(self, account, debit, credit):
        vals = {
            "name": self.env._("Regularization"),
            "account_id": account.id,
            "partner_id": self.env.ref("l10n_es_aeat.res_partner_aeat").id,
        }
        precision = self.env["decimal.precision"].precision_get("Account")
        balance = round(debit - credit, precision)
        vals["debit"] = 0.0 if debit > credit else -balance
        vals["credit"] = balance if debit > credit else 0.0
        return vals

    def _prepare_regularization_extra_move_lines(self):
        return []

    def _prepare_regularization_move_lines(self):
        """Prepare the list of dictionaries for the regularization move lines."""
        self.ensure_one()
        lines = self._process_tax_line_regularization(
            self.tax_line_ids.filtered("to_regularize")
        )
        lines += self._prepare_regularization_extra_move_lines()
        # Write counterpart with the remaining
        debit = sum(x["debit"] for x in lines)
        credit = sum(x["credit"] for x in lines)
        lines.append(
            self._prepare_counterpart_move_line(
                self.counterpart_account_id, debit, credit
            )
        )
        return lines

    def create_regularization_move(self):
        self.ensure_one()
        if not self.counterpart_account_id or not self.journal_id:
            raise exceptions.UserError(
                self.env._("You must fill both journal and counterpart account.")
            )
        move_vals = self._prepare_move_vals()
        line_vals_list = self._prepare_regularization_move_lines()
        move_vals["line_ids"] = [(0, 0, x) for x in line_vals_list]
        self.move_id = self.env["account.move"].create(move_vals)
