# -*- coding: utf-8 -*-
# Copyright 2009 Zikzakmedia S.L. - Jordi Esteve
# Copyright 2013 Joaquin Gutierrez (http://www.gutierrezweb.es)
# Copyright 2015 Tecnativa - Pedro M. Baeza
# Copyright 2017 RGB Consulting
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class JournalEntries(models.AbstractModel):
    _name = 'report.l10n_es_account_financial_report.journal_entries'

    @api.multi
    def render_html(self, data=None):
        account_move_obj = self.env['account.move']
        report_obj = self.env['report']

        if data:
            period_ids = data.get('period_ids', [])
            journal_ids = data.get('journal_ids', [])
        else:  # pragma: no cover
            journal_ids = []
            period_ids = []
            for jp in self:
                journal_ids.append(jp.journal_id.id)
                period_ids.append(jp.period_id.id)

        move_ids = account_move_obj.search(
            [('period_id', 'in', period_ids),
             ('journal_id', 'in', journal_ids),
             ('state', '<>', 'draft')],
            order=data.get('sort_selection', 'date') + ', id')

        report = report_obj._get_report_from_name(
            'l10n_es_account_financial_report.journal_entries')
        docargs = {
            'doc_model': report.model,
            'docs': move_ids,
        }
        return report_obj.render(
            'l10n_es_account_financial_report.journal_entries', docargs)
