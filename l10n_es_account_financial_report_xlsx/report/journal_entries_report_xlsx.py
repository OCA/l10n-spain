# -*- coding: utf-8 -*-
# Copyright 2017 RGB Consulting S.L. (http://www.rgbconsulting.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

try:
    from openerp.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object
from openerp.report import report_sxw
from openerp import _


class JournalEntriesXlsx(ReportXlsx):
    def __init__(self, name, table, rml=False, parser=False, header=True,
                 store=False):
        super(ReportXlsx, self).__init__(
            name, table, rml, parser, header, store)

        self.sheet = None
        self.row_pos = None

        self.format_title = None
        self.format_border_top = None

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
         * format_header_right
         * format_header_italic
         * format_border_top
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'bg_color': '#46C646',
            'border': True
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True
        })
        self.format_header_right = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True,
            'align': 'right'
        })
        self.format_header_italic = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True,
            'italic': True
        })
        self.format_border_top = workbook.add_format({
            'top': 1
        })

    def _write_report_title(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 7, title, self.format_title
        )
        self.row_pos += 2

    def _set_headers(self):
        # Journal
        self.sheet.write_string(self.row_pos, 3, _('Journal'),
                                self.format_header)
        # Partner
        self.sheet.write_string(self.row_pos, 4, _('Partner'),
                                self.format_header)
        # Reference
        self.sheet.write_string(self.row_pos, 5, _('Reference'),
                                self.format_header)
        self.row_pos += 1
        # Entry
        self.sheet.write_string(self.row_pos, 0, _('Entry'),
                                self.format_header)
        # Date
        self.sheet.write_string(self.row_pos, 1, _('Date'), self.format_header)
        # Period
        self.sheet.write_string(self.row_pos, 2, _('Period'),
                                self.format_header)
        # Account
        self.sheet.write_string(self.row_pos, 3, _('Account'),
                                self.format_header_italic)
        # Account name
        self.sheet.write_string(self.row_pos, 4, _('Account name'),
                                self.format_header_italic)
        # Description
        self.sheet.write_string(self.row_pos, 5, _('Description'),
                                self.format_header_italic)
        # Debit
        self.sheet.write_string(self.row_pos, 6, _('Debit'),
                                self.format_header_right)
        # Credit
        self.sheet.write_string(self.row_pos, 7, _('Credit'),
                                self.format_header_right)
        self.row_pos += 1

    def _generate_report_content(self, report_data):
        for move in report_data:
            # Entry
            self.sheet.write_string(self.row_pos, 0, move.name or '',
                                    self.format_border_top)
            self.sheet.set_column(0, 0, 18)
            # Date
            self.sheet.write_string(self.row_pos, 1, move.date or '',
                                    self.format_border_top)
            self.sheet.set_column(1, 1, 12)
            # Period
            self.sheet.write_string(self.row_pos, 2, move.period_id.name or '',
                                    self.format_border_top)
            self.sheet.set_column(2, 2, 12)
            # Journal
            self.sheet.write_string(self.row_pos, 3,
                                    move.journal_id.name or '',
                                    self.format_border_top)
            self.sheet.set_column(3, 3, 30)
            # Partner
            self.sheet.write_string(self.row_pos, 4,
                                    move.partner_id.name or '',
                                    self.format_border_top)
            self.sheet.set_column(4, 4, 40)
            # Reference
            self.sheet.write_string(self.row_pos, 5, move.ref or '',
                                    self.format_border_top)
            self.sheet.set_column(5, 5, 40)
            # Debit
            self.sheet.write_number(self.row_pos, 6, move.amount or 0,
                                    self.format_border_top)
            self.sheet.set_column(6, 6, 12)
            # Credit
            self.sheet.write_number(self.row_pos, 7, move.amount or 0,
                                    self.format_border_top)
            self.sheet.set_column(7, 7, 12)

            self.row_pos += 1
            for line in move.line_id:
                # Account code
                self.sheet.write_string(self.row_pos, 3,
                                        line.account_id.code or '')
                # Account name
                self.sheet.write_string(self.row_pos, 4,
                                        line.account_id.name or '')
                # Line description
                self.sheet.write_string(self.row_pos, 5, line.name or '')
                # Debit
                self.sheet.write_number(self.row_pos, 6, line.debit or 0)
                # Credit
                self.sheet.write_number(self.row_pos, 7, line.credit or 0)
                self.row_pos += 1

    def generate_xlsx_report(self, workbook, data, objects):
        if data:
            period_ids = data.get('period_ids', [])
            journal_ids = data.get('journal_ids', [])
        else:  # pragma: no cover
            journal_ids = []
            period_ids = []
            for jp in objects:
                journal_ids.append(jp.journal_id.id)
                period_ids.append(jp.period_id.id)

        report_data = self.env['account.move'].search(
            [('period_id', 'in', period_ids),
             ('journal_id', 'in', journal_ids),
             ('state', '<>', 'draft')],
            order=data.get('sort_selection', 'date') + ', id')

        # Initial row
        self.row_pos = 0

        # Load formats to workbook
        self._define_formats(workbook)

        # Set report name
        report_name = _('Journal Ledger') + ' - ' + \
            self.env.user.company_id.name
        self.sheet = workbook.add_worksheet(report_name[:31])
        self._write_report_title(report_name)

        # Set headers
        self._set_headers()

        # Generate data
        self._generate_report_content(report_data)


if ReportXlsx != object:
    JournalEntriesXlsx(
        'report.l10n_es_account_financial_report.journal_entries_xlsx',
        'account.journal.period', parser=report_sxw.rml_parse
    )
