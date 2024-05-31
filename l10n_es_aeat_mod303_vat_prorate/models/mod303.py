# Copyright 2023 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# Copyright 2023 Tecnativa - Carolina Fernandez
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

from odoo import _, api, exceptions, fields, models


class L10nEsAeatMod303Report(models.Model):
    _inherit = "l10n.es.aeat.mod303.report"

    casilla_44 = fields.Float(
        string="[44] Prorate regularization",
        default=0,
        states={"done": [("readonly", True)]},
        help="Regularización por aplicación del porcentaje definitivo de prorrata.",
    )
    with_vat_prorate = fields.Boolean(related="company_id.with_vat_prorate")
    vat_prorate_percent = fields.Float(
        string="Definitive VAT prorate percentage",
        default=100,
        readonly=True,
        states={"draft": [("readonly", False)]},
    )
    prorate_account_id = fields.Many2one(
        comodel_name="account.account",
        string="Prorate regularization account",
        help="This account will be the one where charging the regularization of the VAT"
        " prorate.",
        readonly=True,
        states={"calculated": [("readonly", False)]},
    )
    prorate_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Prorate regularization analytic account",
        help="This analytic account will be the one where charging the regularization "
        "of the VAT prorate.",
        readonly=True,
        states={"calculated": [("readonly", False)]},
    )

    @api.constrains("vat_prorate_percent")
    def check_vat_prorate_percent(self):
        if not (0 < self.vat_prorate_percent <= 100):
            raise exceptions.ValidationError(
                _("VAT prorate percent must be between 0.01 and 100")
            )

    def _calculate_casilla_44_mod303_vat_prorate(self):
        self.ensure_one()
        theoretical_prorate = self.company_id.get_prorate(self.date_start)
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
        # Change the amount to deduce and set field 44
        self.total_deducir += diff_amount
        self.casilla_44 = round(result, 2)

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
                    ("company_id", "=", report.company_id.id),
                ],
                limit=1,
            )
        return res

    def _get_move_line_domain(self, date_start, date_end, map_line):
        """Restrict the deductible taxes to the lines that are not prorate ones."""
        res = super()._get_move_line_domain(date_start, date_end, map_line)
        if (
            map_line.field_number in {29, 33, 35, 37, 39, 41}
            and self.company_id.with_vat_prorate
        ):
            res += [("vat_prorate", "=", False)]
        return res

    def _prepare_regularization_extra_move_lines(self):
        """Add the amount of the regularization to the liquidation entry."""
        lines = super()._prepare_regularization_extra_move_lines()
        if self.casilla_44 and self.with_vat_prorate:
            line_vals = {
                "name": _("VAT prorate regularization"),
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
