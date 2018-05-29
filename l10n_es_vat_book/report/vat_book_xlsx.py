# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import models


class VatNumberXlsx(models.AbstractModel):
    _name = 'report.l10n_es_vat_book.l10n_es_vat_book_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        book = objects[0]
        bold = workbook.add_format({'bold': True})

        def fill_table(report_name, lines):
            sheet = workbook.add_worksheet(report_name[:31])
            row = col = 0
            sheet.write(row, col, 'Invoice', bold)
            col += 1
            sheet.write(row, col, 'Date', bold)
            col += 1
            sheet.write(row, col, 'Partner', bold)
            col += 1
            sheet.write(row, col, 'VAT', bold)
            col += 1
            sheet.write(row, col, 'Base', bold)
            col += 1
            sheet.write(row, col, 'Tax', bold)
            col += 1
            sheet.write(row, col, 'Fee', bold)
            col += 1
            sheet.write(row, col, 'Total', bold)
            row = 1
            for line in lines:
                for tax_line in line.tax_line_ids:
                    col = 0
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
            report_name = 'Issued Invoices'
            lines = book.issued_line_ids
            fill_table(report_name, lines)
        if book.rectification_issued_line_ids:
            report_name = 'Issued Rectification Invoices'
            lines = book.rectification_issued_line_ids
            fill_table(report_name, lines)
        if book.received_line_ids:
            report_name = 'Received Invoices'
            lines = book.received_line_ids
            fill_table(report_name, lines)
        if book.rectification_received_line_ids:
            report_name = 'Received Rectification Invoices'
            lines = book.rectification_received_line_ids
            fill_table(report_name, lines)
