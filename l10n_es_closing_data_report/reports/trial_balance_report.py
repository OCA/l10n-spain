# Copyright (C) 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class ReportTrialBalance(models.TransientModel):
    _inherit = 'report_trial_balance'

    move_type = fields.Selection(
        selection=[
            ('opening', 'Opening'),
            ('closing', 'Closing'),
        ],
        default='opening',
    )

    @api.multi
    def print_report(self, report_type):
        self.ensure_one()
        if report_type in ['opening', 'closing']:
            report_name = 'o_c.report_opening_closing_xlsx'
        else:
            return super().print_report(report_type)
        return self.env['ir.actions.report'].search(
            [('report_name', '=', report_name),
             ('report_type', '=', 'xlsx')],
            limit=1).report_action(self, config=False)
