# Copyright 2014 Anubía, soluciones en la nube,SL (http://www.anubia.es)
# Copyright Juan Formoso <jfv@anubia.es>
# Copyright Alejandro Santana <alejandrosantana@anubia.es>
# Copyright Pedro M. Baeza <pedro.baeza@tecnativa.com>
# Copyright 2017 valentin vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models, _
from datetime import date
from xlsxwriter.utility import xl_rowcol_to_cell


class DataReportAccountBalanceReportingXlsxGenericReport(models.AbstractModel):
    _name = 'data.report.account.balance.reporting.xlsx.generic.report'
    _inherit = 'report.report_xlsx.abstract'

    def _define_formats(self, workbook):
        """ Add cell formats to current workbook.
        Available formats:
         * format_title
         * format_header
        """
        self.format_title = workbook.add_format({
            'bold': True,
            'align': 'center',
            'font_size': 14,
            'bg_color': '#FFF58C',
            'border': False
        })
        self.format_header = workbook.add_format({
            'bold': True,
            'bg_color': '#FFFFCC',
            'border': True
        })

    def _write_report_title(self, title):
        self.sheet.merge_range(
            self.row_pos, 0, self.row_pos, 5, title, self.format_title
        )
        self.row_pos += 2

    def _set_headers(self):
        self.row_pos += 1
        # Concept
        self.sheet.write_string(self.row_pos, 0, _('Concept'),
                                self.format_header)
        # Code
        self.sheet.write_string(self.row_pos, 1, _('Code'),
                                self.format_header)
        # Notes
        self.sheet.write_string(self.row_pos, 2, _('Notes'),
                                self.format_header)
        # Current Value
        self.sheet.write_string(self.row_pos, 3, _('Current Value'),
                                self.format_header)
        # Previous Value
        self.sheet.write_string(self.row_pos, 4, _('Previous Value'),
                                self.format_header)
        # Balance
        self.sheet.write_string(self.row_pos, 5, _('Balance'),
                                self.format_header)
        self.row_pos += 1

    def _generate_report_content(self, report_data, zero_lines):
        for line in report_data.line_ids:
            if zero_lines or (line.current_value != 0.00 or
                              line.previous_value != 0.00):
                # Concept
                self.sheet.write_string(self.row_pos, 0, line.display_name or
                                        '')
                self.sheet.set_column(0, 0, 70)
                # Code
                self.sheet.write_string(self.row_pos, 1, line.code or '')
                self.sheet.set_column(1, 1, 12)
                # Notes
                self.sheet.write_string(self.row_pos, 2, line.notes or '')
                self.sheet.set_column(2, 2, 20)
                # Current Value
                self.sheet.write_number(self.row_pos, 3,
                                        line.current_value or 0.00)
                self.sheet.set_column(3, 3, 20)
                # Previous Value
                self.sheet.write_number(self.row_pos, 4,
                                        line.previous_value or 0.00)
                self.sheet.set_column(4, 4, 20)
                # Balance
                row_current_value = xl_rowcol_to_cell(self.row_pos, 3)
                row_previous_value = xl_rowcol_to_cell(self.row_pos, 4)
                self.sheet.write_formula(self.row_pos, 5,
                                         str('=' + row_current_value + '-' +
                                             row_previous_value))
                self.sheet.set_column(5, 5, 20)
                # Change row
                self.row_pos += 1

    def get_zero_lines(self, objects):
        zero_lines = True
        name_module = 'account_balance_reporting.'
        name_report = 'report_account_balance_reporting_default_non_zero'
        inf_zero_line_id = self.env.ref(name_module+name_report)[0].id
        if inf_zero_line_id == objects.report_xml_id.id:
            zero_lines = False
        return zero_lines

    def get_report_name(self, objects):
        report_name = 'Informe Genérico'
        if objects:
            report_name = objects.name.capitalize() + \
                ' - ' + self.env.user.company_id.name + \
                ' - ' + str(date.today())
        return report_name[:31]


class ReportAccountBalanceReportingXlsxGenericReport(models.AbstractModel):
    _name = 'report.account_balance_reporting_xlsx.generic_report'
    _inherit = 'data.report.account.balance.reporting.xlsx.generic.report'

    def generate_xlsx_report(self, workbook, data, objects):
        # Initial row
        self.row_pos = 0
        # Load formats to workbook
        self._define_formats(workbook)
        # Set report name
        report_name = self.get_report_name(objects)
        self.sheet = workbook.add_worksheet(report_name)
        self._write_report_title(report_name)
        # Set headers
        self._set_headers()
        zero_lines = self.get_zero_lines(objects.template_id)
        self._generate_report_content(objects, zero_lines)


class ReportAccountBalanceReportingXlsxWizaGenericReport(models.AbstractModel):
    _name = 'report.account_balance_reporting_xlsx.wizard_generic_report'
    _inherit = 'data.report.account.balance.reporting.xlsx.generic.report'

    def generate_xlsx_report(self, workbook, data, objects):
        # Initial row
        self.row_pos = 0
        # Load formats to workbook
        self._define_formats(workbook)
        # Set report name
        report_name = self.get_report_name(objects.report_id)
        self.sheet = workbook.add_worksheet(report_name)
        self._write_report_title(report_name)
        # Set headers
        self._set_headers()
        zero_lines = self.get_zero_lines(objects)
        self._generate_report_content(objects.report_id, zero_lines)
