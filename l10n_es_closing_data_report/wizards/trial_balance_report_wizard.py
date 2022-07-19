# Copyright (C) 2022 Trey, Kilobytes de Soluciones - Vicent Cubells
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models


class TrialBalanceReportWizard(models.TransientModel):
    _inherit = 'trial.balance.report.wizard'

    opening_closing_move = fields.Boolean(
        string='Opening/Closing Move',
    )
    move_type = fields.Selection(
        selection=[
            ('opening', 'Opening'),
            ('closing', 'Closing'),
        ],
        default='opening',
    )

    @api.multi
    def button_create_move(self):
        self.ensure_one()
        return self._export(self.move_type)

    @api.onchange('opening_closing_move')
    def _onchange_opening_closing_move(self):
        if self.opening_closing_move:
            self.hierarchy_on = 'none'
            self.hide_account_at_0 = True
            self.show_partner_details = False
            self.limit_hierarchy_level = False
            self.hide_parent_hierarchy_level = False
            self.foreign_currency = False
            self.journal_ids = False
            self.account_ids = False
            self.receivable_accounts_only = False
            self.payable_accounts_only = False

    def _prepare_report_trial_balance(self):
        self.ensure_one()
        values = super()._prepare_report_trial_balance()
        values.update({'move_type': self.move_type})
        return values
