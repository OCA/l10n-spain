# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2016,2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, exceptions, fields, models


class L10nEsAeatReportTaxMapping(models.AbstractModel):
    _name = "l10n.es.aeat.report.tax.mapping"
    _inherit = "l10n.es.aeat.report"
    _description = (
        "Inheritable abstract model to add taxes by code mapping in any AEAT report"
    )

    tax_line_ids = fields.One2many(
        comodel_name="l10n.es.aeat.tax.line",
        inverse_name="res_id",
        domain=lambda self: [("model", "=", self._name)],
        auto_join=True,
        readonly=True,
        string="Tax lines",
    )

    def calculate(self):
        res = super().calculate()
        for report in self:
            report.tax_line_ids.unlink()
            report.env.invalidate_all()
            # Buscar configuración de mapeo de impuestos
            tax_code_map = (
                self.env["l10n.es.aeat.map.tax"]
                .sudo()
                .with_context(active_test=False)
                .search(
                    [
                        ("model", "=", report.number),
                        "|",
                        ("date_from", "<=", report.date_start),
                        ("date_from", "=", False),
                        "|",
                        ("date_to", ">=", report.date_end),
                        ("date_to", "=", False),
                    ],
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
        if map_line.sum_type == "credit":
            amount = sum(move_lines.mapped("credit"))
        elif map_line.sum_type == "debit":
            amount = sum(move_lines.mapped("debit"))
        else:  # map_line.sum_type == 'both'
            amount = sum(move_lines.mapped("credit")) - sum(move_lines.mapped("debit"))
        if map_line.inverse:
            amount = (-1.0) * amount
        return {
            "model": self._name,
            "res_id": self.id,
            "map_line_id": map_line.id,
            "amount": amount,
            "move_line_ids": [(6, 0, move_lines.ids)],
        }

    def _get_partner_domain(self):
        return []

    def get_taxes_from_map(self, map_line):
        return self.get_taxes_from_templates(map_line.tax_ids)

    def _get_move_line_domain(self, date_start, date_end, map_line):
        self.ensure_one()
        taxes = self.get_taxes_from_map(map_line)
        move_line_domain = [
            ("company_id", "child_of", self.company_id.id),
            ("date", ">=", date_start),
            ("date", "<=", date_end),
            ("parent_state", "=", "posted"),
        ]
        if map_line.move_type == "regular":
            move_line_domain.append(
                (
                    "move_id.financial_type",
                    "in",
                    ("receivable", "payable", "liquidity", "other"),
                )
            )
        elif map_line.move_type == "refund":
            move_line_domain.append(
                (
                    "move_id.financial_type",
                    "in",
                    ("receivable_refund", "payable_refund"),
                )
            )
        if map_line.field_type == "base":
            move_line_domain.append(("tax_ids", "in", taxes.ids))
        elif map_line.field_type == "amount":
            move_line_domain.append(("tax_line_id", "in", taxes.ids))
        else:  # map_line.field_type == 'both'
            move_line_domain += [
                "|",
                ("tax_line_id", "in", taxes.ids),
                ("tax_ids", "in", taxes.ids),
            ]
        if map_line.account_id:
            account = self.get_account_from_template(map_line.account_id)
            move_line_domain.append(("account_id", "in", account.ids))
        if map_line.sum_type == "debit":
            move_line_domain.append(("debit", ">", 0))
        elif map_line.sum_type == "credit":
            move_line_domain.append(("credit", ">", 0))
        if map_line.exigible_type == "yes":
            move_line_domain.extend(
                (
                    "|",
                    ("move_id.tax_cash_basis_rec_id", "!=", False),
                    "|",
                    ("tax_line_id.tax_exigibility", "!=", "on_payment"),
                    ("tax_ids.tax_exigibility", "!=", "on_payment"),
                )
            )
        elif map_line.exigible_type == "no":
            move_line_domain.extend(
                (
                    ("move_id.tax_cash_basis_rec_id", "=", False),
                    ("tax_line_id.tax_exigibility", "=", "on_payment"),
                    ("tax_ids.tax_exigibility", "=", "on_payment"),
                )
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
    def _prepare_regularization_move_line(self, account_group):
        return {
            "name": account_group["account_id"][1],
            "account_id": account_group["account_id"][0],
            "debit": account_group["credit"],
            "credit": account_group["debit"],
        }

    def _process_tax_line_regularization(self, tax_lines):
        self.ensure_one()
        groups = self.env["account.move.line"].read_group(
            [
                ("id", "in", tax_lines.move_line_ids.ids),
                ("parent_state", "=", "posted"),
            ],
            ["debit", "credit", "account_id"],
            ["account_id"],
        )
        lines = []
        for group in groups:
            balance = group["debit"] - group["credit"]
            if balance:
                group["debit"] = balance if balance > 0 else 0
                group["credit"] = -balance if balance < 0 else 0
                lines.append(self._prepare_regularization_move_line(group))
        return lines

    @api.model
    def _prepare_counterpart_move_line(self, account, debit, credit):
        vals = {
            "name": _("Regularization"),
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
                _("You must fill both journal and counterpart account.")
            )
        move_vals = self._prepare_move_vals()
        line_vals_list = self._prepare_regularization_move_lines()
        move_vals["line_ids"] = [(0, 0, x) for x in line_vals_list]
        self.move_id = self.env["account.move"].create(move_vals)
