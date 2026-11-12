# Copyright 2023 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

import datetime
import math

from odoo import api, exceptions, fields, models
from odoo.fields import Domain
from odoo.tools import float_is_zero


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    casilla_44 = fields.Float(
        string="[44] Prorate regularization",
        default=0,
        readonly=True,
        help="Regularización por aplicación del porcentaje definitivo de prorrata.",
    )
    with_vat_prorate = fields.Boolean(related="company_id.with_vat_prorate")
    prorate_id = fields.Many2one(
        comodel_name="res.company.vat.prorate",
        compute="_compute_prorate_id",
        ondelete="restrict",
        store=True,
    )
    with_special_vat_prorate = fields.Boolean(compute="_compute_prorate_id", store=True)
    vat_prorate_percent = fields.Float(
        string="Definitive VAT prorate percentage",
        default=100,
        readonly=True,
    )
    prorate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Prorate regularization account",
        help="This account will be the one where charging the regularization of the VAT"
        " prorate.",
        readonly=True,
    )
    prorate_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Prorate regularization analytic account",
        help="This analytic account will be the one where charging the regularization "
        "of the VAT prorate.",
        readonly=True,
    )

    @api.depends(
        "company_id.vat_prorate_ids",
        "company_id.with_vat_prorate",
        "date_start",
    )
    def _compute_prorate_id(self):
        for rec in self:
            if rec.company_id.with_vat_prorate:
                prorate_date = rec.date_start or fields.Date.today()
                rec.prorate_id = rec.company_id.get_prorate(prorate_date)
                rec.with_special_vat_prorate = rec.prorate_id.type == "special"
            else:
                rec.prorate_id = rec.with_special_vat_prorate = False

    @api.constrains("vat_prorate_percent")
    def check_vat_prorate_percent(self):
        if not (0 <= self.vat_prorate_percent <= 100):
            raise exceptions.ValidationError(
                self.env._("VAT prorate percent must be between 0.00 and 100")
            )

    def _general_prorate_method(self):
        self.ensure_one()
        theoretical_prorate = self.prorate_id.vat_prorate
        if float_is_zero(theoretical_prorate, precision_digits=2):
            raise exceptions.ValidationError(
                self.env._(
                    "Prorate percentage not found, or it's 0. "
                    "Please review the company's prorate adjustments."
                )
            )
        diff_perc = self.vat_prorate_percent - theoretical_prorate
        if not diff_perc:
            return
        result = 0
        # Get the difference for the previous reports
        prev_reports = self._get_previous_fiscalyear_reports(self.date_start)
        for report in prev_reports:
            result += diff_perc * report.total_deducir / theoretical_prorate
        # Get the diff for this declaration (the last of the year)
        diff_amount = round(diff_perc * self.total_deducir / theoretical_prorate, 2)
        result += diff_amount
        # Set field 44 and add it to the amount to deduce ([45] includes [44])
        self.casilla_44 = round(result, 2)
        self.total_deducir += self.casilla_44

    def _special_prorate_method(self):
        self.ensure_one()
        domain = Domain(
            [
                ("company_id", "child_of", self.company_id.id),
                (
                    "date",
                    ">=",
                    datetime.date(year=self.date_start.year, month=1, day=1),
                ),
                (
                    "date",
                    "<=",
                    datetime.date(year=self.date_end.year, month=12, day=31),
                ),
                ("parent_state", "=", "posted"),
                ("vat_prorate", "=", True),
            ]
        )
        company_prorate = self.prorate_id.vat_prorate
        theoretical_prorate = 100 - company_prorate
        diff_perc = self.vat_prorate_percent - company_prorate
        # Refunds take their prorate out (credit), as the bills put it (debit)
        theoretical_result = sum(
            self.env["account.move.line"].search(domain).mapped("balance")
        )
        result = theoretical_result * diff_perc / theoretical_prorate

        self.total_deducir += result
        self.casilla_44 = round(result, 2)

    def _calculate_casilla_44_mod303_vat_prorate(self):
        self.ensure_one()
        if self.with_special_vat_prorate:
            self._special_prorate_method()
        else:
            self._general_prorate_method()

    def calculate(self):
        """Calculate the field 44 according the definitive one and adjust results."""
        res = super().calculate()
        for report in self:
            report.casilla_44 = 0
            if report.period_type not in {"4T", "12"} or not report.with_vat_prorate:
                continue
            report._calculate_casilla_44_mod303_vat_prorate()
            account_number = "6391%" if report.casilla_44 >= 0 else "6341%"
            # Choose default account according result
            report.prorate_account_id = self.env["account.account"].search(
                [
                    ("code", "like", account_number),
                    ("company_ids", "=", report.company_id.id),
                ],
                limit=1,
            )
        return res

    def _get_move_line_domain(self, date_start, date_end, map_line):
        """Restrict the deductible taxes to the lines that are not prorate ones."""
        res = super()._get_move_line_domain(date_start, date_end, map_line)
        if (
            map_line.field_number in {29, 31, 33, 35, 37, 39, 41, 42}
            and self.company_id.with_vat_prorate
        ):
            res &= Domain("vat_prorate", "=", False)
        return res

    def _prepare_regularization_extra_move_lines(self):
        """Add the amount of the regularization to the liquidation entry."""
        lines = super()._prepare_regularization_extra_move_lines()
        if self.casilla_44 and self.with_vat_prorate:
            line_vals = {
                "name": self.env._("VAT prorate regularization"),
                "account_id": self.prorate_account_id.id,
                "debit": -self.casilla_44 if self.casilla_44 < 0 else 0.0,
                "credit": self.casilla_44 if self.casilla_44 > 0 else 0.0,
            }
            # Add analytic_distribution only if prorate_analytic_account_id is set
            if self.prorate_analytic_account_id:
                line_vals["analytic_distribution"] = {
                    self.prorate_analytic_account_id.id: 100
                }
            lines.append(line_vals)
        return lines

    def _get_vat_prorate_sale_taxes(self, domain):
        Tax = self.env["account.tax"].with_context(active_test=False)
        return Tax.search(
            Domain.AND(
                [
                    Domain("company_id", "child_of", self.company_id.root_id.id),
                    Domain("type_tax_use", "=", "sale"),
                    domain,
                ]
            )
        )

    def _get_vat_prorate_taxed_taxes(self):
        """Sale taxes whose base gives the right to deduct (art. 94.Uno LIVA), from
        the tax type and the exempt reason that Odoo core sets on every Spanish tax:
        subject operations, the exempt ones of arts. 21 to 25 (E2 to E5) and the
        ones not subject by location rules."""
        Tax = self.env["account.tax"]
        return self._get_vat_prorate_sale_taxes(
            Domain.OR(
                [
                    Domain("l10n_es_type", "in", Tax._l10n_es_get_sujeto_tax_types()),
                    Domain("l10n_es_type", "=", "exento")
                    & Domain("l10n_es_exempt_reason", "in", ["E2", "E3", "E4", "E5"]),
                    Domain("l10n_es_type", "=", "no_sujeto_loc"),
                ]
            )
        )

    def _get_vat_prorate_exempt_taxes(self):
        """Sale taxes whose base doesn't give the right to deduct but counts in the
        denominator (art. 104.Dos.2.º LIVA): the exempt ones of art. 20 (E1) and the
        other exemptions (E6). Operations not subject by art. 7 are left out of both
        terms (art. 104.Tres.5.º)."""
        return self._get_vat_prorate_sale_taxes(
            Domain("l10n_es_type", "=", "exento")
            & Domain("l10n_es_exempt_reason", "in", ["E1", "E6"])
        )

    def _get_vat_prorate_base(self, taxes, date_from, date_to):
        """Base of the posted move lines of the period with any of the given taxes,
        with the conditions of the AEAT engine for a base line of every move type
        (see ``_get_move_line_domain``)."""
        domain = Domain.AND(
            [
                Domain("company_id", "child_of", self.company_id.id),
                Domain("date", ">=", date_from),
                Domain("date", "<=", date_to),
                Domain("parent_state", "=", "posted"),
                Domain("tax_ids", "in", taxes.ids),
                Domain.OR(
                    [
                        Domain("move_id.tax_cash_basis_rec_id", "!=", False),
                        Domain("tax_line_id.tax_exigibility", "!=", "on_payment"),
                        Domain("tax_ids.tax_exigibility", "!=", "on_payment"),
                    ]
                ),
                self._get_partner_domain(),
            ]
        )
        return -sum(self.env["account.move.line"].search(domain).mapped("balance"))

    def button_compute(self):
        self.ensure_one()
        date_from = f"{self.year}-01-01"
        date_to = f"{self.year}-12-31"
        taxed = self._get_vat_prorate_base(
            self._get_vat_prorate_taxed_taxes(), date_from, date_to
        )
        exempt = self._get_vat_prorate_base(
            self._get_vat_prorate_exempt_taxes(), date_from, date_to
        )
        total_base = taxed + exempt
        self.vat_prorate_percent = (
            math.ceil(taxed / total_base * 100) if total_base > 0 else 100
        )
        return True
