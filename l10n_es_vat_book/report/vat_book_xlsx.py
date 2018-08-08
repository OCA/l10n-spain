# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object
from odoo import _
from odoo.report import report_sxw


class VatNumberXlsx(ReportXlsx):

    def generate_xlsx_report(self, workbook, data, objects):
        book = objects[0]
        bold = workbook.add_format({'bold': True})

        def fill_table(sheet_name, lines, received_lines=False):
            sheet = workbook.add_worksheet(sheet_name[:31])
            row = col = 0
            xlsx_header = [
                _('Invoice'),
                _('Date'),
                _('Partner'),
                _('VAT'),
                _('Base'),
                _('Tax'),
                _('Fee'),
                _('Total'),
            ]
            if received_lines:
                xlsx_header.insert(0, _('Reference'))
            for col_header in xlsx_header:
                sheet.write(row, col, col_header, bold)
                col += 1

            row = 1
            for line in lines:
                for tax_line in line.tax_line_ids:
                    col = 0
                    if received_lines:
                        sheet.write(row, col, line.invoice_id.reference)
                        col += 1
                    sheet.write(row, col, line.invoice_id.number)
                    col += 1
                    sheet.write(row, col, line.invoice_date)
                    col += 1
                    sheet.write(row, col, line.partner_id.name)
                    col += 1
                    sheet.write(row, col, line.vat_number)
                    col += 1
                    sheet.write(row, col, tax_line.base_amount)
                    col += 1
                    sheet.write(row, col, tax_line.tax_id.name)
                    col += 1
                    sheet.write(row, col, tax_line.tax_amount)
                    col += 1
                    sheet.write(row, col, tax_line.total_amount)
                    row += 1

        if book.issued_line_ids:
            report_name = _('Issued Invoices')
            lines = book.issued_line_ids
            fill_table(report_name, lines)
        if book.rectification_issued_line_ids:
            report_name = _('Issued Refund Invoices')
            lines = book.rectification_issued_line_ids
            fill_table(report_name, lines)
        if book.received_line_ids:
            report_name = _('Received Invoices')
            lines = book.received_line_ids
            fill_table(report_name, lines, received_lines=True)
        if book.rectification_received_line_ids:
            report_name = _('Received Refund Invoices')
            lines = book.rectification_received_line_ids
            fill_table(report_name, lines, received_lines=True)


if ReportXlsx != object:
    VatNumberXlsx(
        'report.l10n_es_vat_book.l10n_es_vat_book_xlsx',
        'l10n.es.vat.book', parser=report_sxw.rml_parse,
    )
