# -*- coding: utf-8 -*-
# Copyright 2009 Zikzakmedia S.L. - Jordi Esteve
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2017 RGB Consulting
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, fields, models, exceptions, _


class AccountJournalEntriesReport(models.TransientModel):
    _name = "account.journal.entries.report"
    _description = "Print journal by entries"

    @api.model
    def _default_journal_ids(self):
        return self.env['account.journal'].search([])

    journal_ids = fields.Many2many(
        comodel_name='account.journal',
        string='Journal', required=True, default=_default_journal_ids,
    )
    period_ids = fields.Many2many(
        comodel_name='account.period',
        string='Period'
    )
    sort_selection = fields.Selection(
        [('date', 'By date'),
         ('name', 'By entry number'),
         ('ref', 'By reference number')],
        string='Entries Sorted By', required=True, default='name',
    )
    landscape = fields.Boolean(string='Landscape mode', default=True)

    @api.multi
    def _check_data(self):
        if not self.period_ids and not self.journal_ids:
            return False
        period_obj = self.env['account.journal.period']
        for journal in self.journal_ids:
            for period in self.period_ids:
                ids_journal_period = period_obj.search(
                    [('journal_id', '=', journal.id),
                     ('period_id', '=', period.id)])
                if ids_journal_period:
                    return True
        return False

    @api.multi
    def print_report(self):
        """Print report."""

        # Check data
        if not self._check_data():
            raise exceptions.Warning(
                _('No data available'),
                _('No records found for your selection!'))

        report_name = 'l10n_es_account_financial_report.journal_entries'

        # Call report
        data = self.read()[0]
        return self.env['report'].with_context(
            {'landscape': self.landscape}).get_action(self, report_name,
                                                      data=data)
