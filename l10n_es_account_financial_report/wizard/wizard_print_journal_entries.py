# -*- encoding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp.osv import orm, fields
from openerp.tools.translate import _


class AccountJournalEntriesReport(orm.TransientModel):
    _name = "account.journal.entries.report"
    _description = "Print journal by entries"

    _columns = {
        'journal_ids': fields.many2many(
            'account.journal', 'account_journal_entries_journal_rel',
            'acc_journal_entries_id', 'journal_id', 'Journal', required=True),
        'period_ids': fields.many2many(
            'account.period', 'account_journal_entries_account_period_rel',
            'acc_journal_entries_id', 'account_period_id', 'Period'),
        'sort_selection': fields.selection(
            [('date', 'By date'),
             ('name', 'By entry number'),
             ('ref', 'By reference number')], 'Entries Sorted By',
            required=True),
        'landscape': fields.boolean('Landscape mode')
    }

    def default_get(self, cr, uid, fields, context=None):
        return {
            'sort_selection': 'name',
            'landscape': True,
            'journal_ids': self.pool['account.journal'].search(
                cr, uid, [], context=context),
            'period_ids': self.pool['account.period'].search(
                cr, uid,
                [('fiscalyear_id', '=',
                  self.pool['account.fiscalyear'].find(cr, uid))],
                context=context),
        }

    def _check_data(self, cr, uid, ids, context=None):
        if not ids:
            return False
        data = self.browse(cr, uid, ids[0], context=context)
        if not data.period_ids and not data.journal_ids:
            return False
        period_obj = self.pool['account.journal.period']
        for journal in data.journal_ids:
            for period in data.period_ids:
                ids_journal_period = period_obj.search(
                    cr, uid, [('journal_id', '=', journal.id),
                              ('period_id', '=', period.id)], context=context)
                if ids_journal_period:
                    return True
        return False

    def _check(self, cr, uid, ids, context=None):
        if not ids:
            return False
        current_obj = self.browse(cr, uid, ids[0], context=context)
        return 'report_landscape' if current_obj.landscape else 'report'

    def print_report(self, cr, uid, ids, context=None):
        """Print report."""
        if context is None:
            context = {}
        data = self.read(cr, uid, ids[0], context=context)
        datas = {
            'ids': context.get('active_ids', []),
            'model': 'ir.ui.menu',
            'form': data,
        }
        if not self._check_data(cr, uid, ids, context=context):
            raise orm.except_orm(
                _('No data available'),
                _('No records found for your selection!'))
        if self._check(cr, uid, ids, context=context) == 'report_landscape':
            report_name = 'account.journal.entries.report.wzd1'
        else:
            report_name = 'account.journal.entries.report.wzd'
        return {
            'type': 'ir.actions.report.xml',
            'report_name': report_name,
            'datas': datas,
            'context': context,
        }
