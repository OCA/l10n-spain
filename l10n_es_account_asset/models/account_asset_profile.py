# Copyright 2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.tools import float_compare


class AccountAssetProfile(models.Model):
    _inherit = 'account.asset.profile'

    METHOD_PERIOD_MAPPING = {
        'month': 1,
        'quarter': 4,
        'year': 12,

    }

    @api.model
    def _selection_method_time(self):
        res = super()._selection_method_time()
        res.append(('percentage', _('Fixed percentage')))
        return res

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

    @api.depends('annual_percentage', 'method_period')
    def _compute_method_percentage(self):
        for profile in self:
            profile.method_percentage = (
                profile.annual_percentage * profile.METHOD_PERIOD_MAPPING.get(
                    profile.method_period, 12,
                ) / 12
            )

    @api.onchange('method_percentage')
    def _inverse_method_percentage(self):
        for profile in self:
            new_percentage = (
                profile.method_percentage * 12 /
                profile.METHOD_PERIOD_MAPPING.get(profile.method_period, 12)
            )
            # Only change amount when significant delta
            if float_compare(new_percentage, self.annual_percentage, 2) != 0:
                self.annual_percentage = new_percentage

    _sql_constraints = [
        ('annual_percentage',
         'CHECK (annual_percentage > 0 and annual_percentage <= 100)',
         'Wrong percentage!'),
    ]
