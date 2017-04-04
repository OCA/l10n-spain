# -*- coding: utf-8 -*-
# Copyright 2017 RGB Consulting S.L. (http://www.rgbconsulting.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models, exceptions, _


class AccountJournalEntriesXlsx(models.TransientModel):
    _inherit = 'account.journal.entries.report'

    @api.multi
    def print_report_xlsx(self):
        """Print report XLSX"""

        # Check data
        if not self._check_data():
            raise exceptions.Warning(
                _('No data available'),
                _('No records found for your selection!'))

        # Call report
        data = self.read()[0]
        report_name = 'l10n_es_account_financial_report.journal_entries_xlsx'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': data}
