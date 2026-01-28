# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import api, exceptions, fields, models


class L10nEsAeatMod390Report(models.Model):
    _inherit = "l10n.es.aeat.mod390.report"

    casilla_522 = fields.Float(
        string="[522] Prorate regularization",
        default=0,
        readonly=True,
        help="Regularización por aplicación porcentaje definitivo de prorrata.",
    )
    with_vat_prorate = fields.Boolean(related="company_id.with_vat_prorate")
    vat_prorate_percent = fields.Float(
        string="Definitive VAT prorate percentage",
        default=100,
        readonly=True,
    )

    @api.depends(
        "company_id.vat_prorate_ids",
        "company_id.with_vat_prorate",
        "date_start",
    )
    def _get_company_prorates(self):
        self.ensure_one()
        if self.company_id.with_vat_prorate:
            return self.env["res.company.vat.prorate"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("date", "<=", self.date_end),
                    ("date", ">=", self.date_start),
                ],
            )

    @api.constrains("vat_prorate_percent")
    def check_vat_prorate_percent(self):
        if not (0 <= self.vat_prorate_percent <= 100):
            raise exceptions.ValidationError(
                self.env._("VAT prorate percent must be between 0.00 and 100")
            )

    def _calculate_casilla_522_mod390_vat_prorate(self):
        self.ensure_one()
        company_prorates = self._get_company_prorates()
        result = 0
        prorate_period_qty = len(company_prorates)
        for index, company_prorate in enumerate(company_prorates):
            if index > prorate_period_qty - 1:
                date_end = company_prorates[index + 1].date
            date_end = self.date_end
            result += self._calculate_vat_prorate_diff(
                company_prorate.vat_prorate, company_prorate.date, date_end
            )
        self.casilla_522 = round(result, 2)

    def _calculate_vat_prorate_diff(self, theoretical_prorate, date_start, date_end):
        diff_perc = self.vat_prorate_percent - theoretical_prorate
        if not diff_perc:
            return 0
        domain = [
            ("company_id", "child_of", self.company_id.id),
            ("date", ">=", date_start),
            ("date", "<=", date_end),
            ("parent_state", "=", "posted"),
            ("vat_prorate", "=", True),
        ]
        total_prorate = sum(
            self.env["account.move.line"].search(domain).mapped("debit")
        )
        total_deducir = total_prorate / (1 - theoretical_prorate / 100) - total_prorate
        return round(diff_perc * total_deducir / theoretical_prorate, 2)

    def calculate(self):
        """Calculate the field 522 according the definitive one and adjust results."""
        res = super().calculate()
        for report in self:
            report.casilla_522 = 0
            if report.period_type != "0A" or not report.with_vat_prorate:
                continue
            report._calculate_casilla_522_mod390_vat_prorate()
        return res
