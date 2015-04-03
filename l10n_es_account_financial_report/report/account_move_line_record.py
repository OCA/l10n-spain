# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.report import report_sxw
import time


class JournalPrint(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context=None):
        super(JournalPrint, self).__init__(cr, uid, name, context=context)
        self.localcontext['time'] = time
        self.localcontext['lang'] = context.get('lang')

    def set_context(self, objects, data, ids, report_type=None):
        if data['model'] == 'ir.ui.menu':
            period_ids = data['form']['period_ids']
            journal_ids = data['form']['journal_ids']
            move_ids = self.pool['account.move'].search(
                self.cr, self.uid, [('period_id', 'in', period_ids),
                                    ('journal_id', 'in', journal_ids),
                                    ('state', '<>', 'draft')],
                order=data['form']['sort_selection'] + ', id')
        else:
            move_ids = []
            journalperiods = self.pool['account.journal.period'].browse(
                self.cr, self.uid, ids)
            for jp in journalperiods:
                move_ids = self.pool['account.move'].search(
                    self.cr, self.uid, [('period_id', '=', jp.period_id.id),
                                        ('journal_id', '=', jp.journal_id.id),
                                        ('state', '<>', 'draft')],
                    order='date,id')
        objects = self.pool['account.move'].browse(self.cr, self.uid, move_ids)
        super(JournalPrint, self).set_context(objects, data, ids, report_type)


report_sxw.report_sxw(
    'report.account.journal.entries.report.wzd', 'account.journal.period',
    'l10n_es_account_financial_report/report/account_move_line_record.rml',
    parser=JournalPrint, header=False)
report_sxw.report_sxw(
    'report.account.journal.entries.report.wzd1', 'account.journal.period',
    'l10n_es_account_financial_report/report/account_move_line_record_h.rml',
    parser=JournalPrint, header=False)
