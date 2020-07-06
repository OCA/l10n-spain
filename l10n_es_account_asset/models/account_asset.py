# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2012-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from datetime import date
from odoo import api, fields, models
from odoo.tools import float_compare
from dateutil.relativedelta import relativedelta


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    annual_percentage = fields.Float(
        string='Annual depreciation percentage',
        digits=(3, 8),
        default=100.0,
    )
    method_percentage = fields.Float(
        string='Depreciation percentage',
        digits=(3, 8),
        compute="_compute_method_percentage",
        inverse="_inverse_method_percentage",
        store=True,
    )

    _sql_constraints = [
        ('annual_percentage',
         'CHECK (annual_percentage > 0 and annual_percentage <= 100)',
         'Wrong percentage!'),
    ]

    @api.depends('annual_percentage', 'method_period')
    def _compute_method_percentage(self):
        mapping = self.env['account.asset.profile'].METHOD_PERIOD_MAPPING
        for asset in self:
            asset.method_percentage = (
                asset.annual_percentage *
                mapping.get(asset.method_period, 12) / 12
            )

    @api.onchange('method_percentage')
    def _inverse_method_percentage(self):
        mapping = self.env['account.asset.profile'].METHOD_PERIOD_MAPPING
        for asset in self:
            new_percentage = (
                asset.method_percentage * 12 /
                mapping.get(asset.method_period, 12)
            )
            if new_percentage > 100:
                new_percentage = 100
            # Only change amount when significant delta
            if float_compare(new_percentage, self.annual_percentage, 2) != 0:
                self.annual_percentage = new_percentage

    @api.onchange('profile_id')
    def _onchange_profile_id(self):
        res = super()._onchange_profile_id()
        if self.profile_id:
            self.method_percentage = self.profile_id.method_percentage
        return res

    def _get_depreciation_stop_date(self, depreciation_start_date):
        """Compute stop date for the added method 'Percentage'."""
        if self.method_time == 'percentage':
            number = 0
            percentage = 100.0
            stop_date = depreciation_start_date
            while percentage > 0:
                if number == 0 and self.prorata:
                    days = (
                        date(stop_date.year, month=12, day=31) -
                        stop_date
                    ).days + 1
                    year_days = (
                        date(stop_date.year, month=12, day=31) -
                        date(stop_date.year, month=1, day=1)
                    ).days + 1
                    percentage -= self.annual_percentage * days / year_days
                    stop_date += relativedelta(day=31, month=12)
                else:
                    if (float_compare(
                            percentage - self.annual_percentage, 0.0, 8) >= 0):
                        stop_date += relativedelta(years=1)
                    else:
                        # Remaining percentage is not whole year
                        year_days = (
                            date(stop_date.year + 1, month=12, day=31) -
                            date(stop_date.year + 1, month=1, day=1)
                        ).days + 1
                        days = int(
                            year_days * percentage / self.annual_percentage
                        )
                        stop_date += relativedelta(days=days)
                    percentage -= self.annual_percentage
                number += 1
            return stop_date
        return super()._get_depreciation_stop_date(depreciation_start_date)

    def _compute_line_dates(self, table, start_date, stop_date):
        """Add last depreciation date when method is percentage."""
        line_dates = super()._compute_line_dates(table, start_date, stop_date)
        if self.method_time == 'percentage':
            if not line_dates or line_dates[-1] < stop_date:
                if self.method_period == 'month':
                    line_date = stop_date + relativedelta(day=31)
                if self.method_period == 'quarter':
                    m = [x for x in [3, 6, 9, 12] if x >= stop_date.month][0]
                    line_date = stop_date + relativedelta(month=m, day=31)
                elif self.method_period == 'year':
                    line_date = stop_date + relativedelta(month=12, day=31)
                line_dates.append(line_date)
        return line_dates

    def _compute_depreciation_amount_per_fiscal_year(
            self, table, line_dates, depreciation_start_date,
            depreciation_stop_date
    ):
        """"Simulate the computation like year one."""
        is_changed = self.method_time == 'percentage'
        if is_changed:
            self.method_time = 'year'
        table = super()._compute_depreciation_amount_per_fiscal_year(
            table, line_dates, depreciation_start_date,
            depreciation_stop_date,
        )
        if is_changed:
            self.method_time = 'percentage'
        return table

    def _compute_depreciation_table_lines(self, table, depreciation_start_date,
                                          depreciation_stop_date, line_dates):
        """"Simulate the computation like year one."""
        is_changed = self.method_time == 'percentage'
        if is_changed:
            self.method_time = 'year'
        super(
            AccountAssetAsset, self.with_context(
                use_percentage=True))._compute_depreciation_table_lines(
            table, depreciation_start_date, depreciation_stop_date, line_dates,
        )
        if is_changed:
            self.method_time = 'percentage'

    def _get_amount_linear(
            self, depreciation_start_date, depreciation_stop_date, entry):
        if self.env.context.get('use_percentage', False):
            return self.depreciation_base * self.annual_percentage / 100
        return super(AccountAssetAsset, self)._get_amount_linear(
            depreciation_start_date, depreciation_stop_date, entry)
