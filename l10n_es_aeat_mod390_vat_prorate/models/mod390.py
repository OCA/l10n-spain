# Copyright 2025 Moduon Team S.L.
# Copyright 2026 Tecnativa - Christian Ramos
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

import math

from odoo import api, exceptions, fields, models

ACTIVITY_PRORATE_TYPES = [
    ("G", "General"),
    ("E", "Especial"),
]


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

    first_dev_activity = fields.Char(string="1 - Actividad desarrollada", size=40)
    first_dev_activity_cnae_code = fields.Char(string="1 - Código CNAE [114]", size=3)
    first_dev_activity_operation_amount = fields.Float(
        string="1 - Importe operaciones [115]",
        digits=(15, 2),
    )
    first_dev_activity_operation_amount_deductible = fields.Float(
        string="1 - Importe de operaciones con derecho a deducción [116]",
        digits=(15, 2),
    )
    first_dev_activity_prorate_type = fields.Selection(
        ACTIVITY_PRORATE_TYPES,
        string="1 - Tipo de prorrata [117]",
    )
    first_dev_activity_prorate_percent = fields.Float(
        string="1 - % de prorrata [118]",
        readonly=True,
        compute="_compute_dev_activity_first_prorate_percentage",
    )
    second_dev_activity = fields.Char(string="2 - Actividad desarrollada", size=40)
    second_dev_activity_cnae_code = fields.Char(string="2 - Código CNAE [114]", size=3)
    second_dev_activity_operation_amount = fields.Float(
        string="2 - Importe operaciones [115]",
        digits=(15, 2),
    )
    second_dev_activity_operation_amount_deductible = fields.Float(
        string="2 - Importe de operaciones con derecho a deducción [116]",
        digits=(15, 2),
    )
    second_dev_activity_prorate_type = fields.Selection(
        ACTIVITY_PRORATE_TYPES,
        string="2 - Tipo de prorrata [117]",
    )
    second_dev_activity_prorate_percent = fields.Float(
        string="2 - % de prorrata [118]",
        readonly=True,
        compute="_compute_dev_activity_second_prorate_percentage",
    )
    third_dev_activity = fields.Char(string="3 - Actividad desarrollada", size=40)
    third_dev_activity_cnae_code = fields.Char(string="3 - Código CNAE [114]", size=3)
    third_dev_activity_operation_amount = fields.Float(
        string="3 - Importe operaciones [115]",
        digits=(15, 2),
    )
    third_dev_activity_operation_amount_deductible = fields.Float(
        string="3 - Importe de operaciones con derecho a deducción [116]",
        digits=(15, 2),
    )
    third_dev_activity_prorate_type = fields.Selection(
        ACTIVITY_PRORATE_TYPES,
        string="3 - Tipo de prorrata [117]",
    )
    third_dev_activity_prorate_percent = fields.Float(
        string="3 - % de prorrata [118]",
        readonly=True,
        compute="_compute_dev_activity_third_prorate_percentage",
    )
    fourth_dev_activity = fields.Char(string="4 - Actividad desarrollada", size=40)
    fourth_dev_activity_cnae_code = fields.Char(string="4 - Código CNAE [114]", size=3)
    fourth_dev_activity_operation_amount = fields.Float(
        string="4 - Importe operaciones [115]",
        digits=(15, 2),
    )
    fourth_dev_activity_operation_amount_deductible = fields.Float(
        string="4 - Importe de operaciones con derecho a deducción [116]",
        digits=(15, 2),
    )
    fourth_dev_activity_prorate_type = fields.Selection(
        ACTIVITY_PRORATE_TYPES,
        string="4 - Tipo de prorrata [117]",
    )
    fourth_dev_activity_prorate_percent = fields.Float(
        string="4 - % de prorrata [118]",
        readonly=True,
        compute="_compute_dev_activity_fourth_prorate_percentage",
    )
    fifth_dev_activity = fields.Char(string="5 - Actividad desarrollada", size=40)
    fifth_dev_activity_cnae_code = fields.Char(string="5 - Código CNAE [114]", size=3)
    fifth_dev_activity_operation_amount = fields.Float(
        string="5 - Importe operaciones [115]",
        digits=(15, 2),
    )
    fifth_dev_activity_operation_amount_deductible = fields.Float(
        string="5 - Importe de operaciones con derecho a deducción [116]",
        digits=(15, 2),
    )
    fifth_dev_activity_prorate_type = fields.Selection(
        ACTIVITY_PRORATE_TYPES,
        string="5 - Tipo de prorrata [117]",
    )
    fifth_dev_activity_prorate_percent = fields.Float(
        string="5 - % de prorrata [118]",
        readonly=True,
        compute="_compute_dev_activity_fifth_prorate_percentage",
    )

    @api.depends(
        "first_dev_activity_operation_amount",
        "first_dev_activity_operation_amount_deductible",
    )
    def _compute_dev_activity_first_prorate_percentage(self):
        for record in self:
            record.first_dev_activity_prorate_percent = (
                self._get_dev_activity_prorate_percentage(
                    record.first_dev_activity_operation_amount,
                    record.first_dev_activity_operation_amount_deductible,
                )
            )

    @api.depends(
        "second_dev_activity_operation_amount",
        "second_dev_activity_operation_amount_deductible",
    )
    def _compute_dev_activity_second_prorate_percentage(self):
        for record in self:
            record.second_dev_activity_prorate_percent = (
                self._get_dev_activity_prorate_percentage(
                    record.second_dev_activity_operation_amount,
                    record.second_dev_activity_operation_amount_deductible,
                )
            )

    @api.depends(
        "third_dev_activity_operation_amount",
        "third_dev_activity_operation_amount_deductible",
    )
    def _compute_dev_activity_third_prorate_percentage(self):
        for record in self:
            record.third_dev_activity_prorate_percent = (
                self._get_dev_activity_prorate_percentage(
                    record.third_dev_activity_operation_amount,
                    record.third_dev_activity_operation_amount_deductible,
                )
            )

    @api.depends(
        "fourth_dev_activity_operation_amount",
        "fourth_dev_activity_operation_amount_deductible",
    )
    def _compute_dev_activity_fourth_prorate_percentage(self):
        for record in self:
            record.fourth_dev_activity_prorate_percent = (
                self._get_dev_activity_prorate_percentage(
                    record.fourth_dev_activity_operation_amount,
                    record.fourth_dev_activity_operation_amount_deductible,
                )
            )

    @api.depends(
        "fifth_dev_activity_operation_amount",
        "fifth_dev_activity_operation_amount_deductible",
    )
    def _compute_dev_activity_fifth_prorate_percentage(self):
        for record in self:
            record.fifth_dev_activity_prorate_percent = (
                self._get_dev_activity_prorate_percentage(
                    record.fifth_dev_activity_operation_amount,
                    record.fifth_dev_activity_operation_amount_deductible,
                )
            )

    def _get_dev_activity_prorate_percentage(self, amount, amount_deductible):
        if amount > 0 and amount_deductible > 0:
            return math.ceil((amount_deductible / amount) * 100)
        return 0.0

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
