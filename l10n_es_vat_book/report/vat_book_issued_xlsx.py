# Copyright 2019 Ignacio Ibeas <ignacio@acysos.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models
from datetime import datetime

EUROPE = ['AT', 'BE', 'BG', 'CY', 'CZ', 'DE', 'DK', 'EE', 'EL', 'FI', 'FR',
          'GB', 'HR', 'HU', 'IE', 'IT', 'LT', 'LU', 'LV', 'MT', 'NL', 'PL',
          'PT', 'RO', 'SE', 'SI', 'SK']

class VatBookIssuedXlsx(models.AbstractModel):
    _name = 'report.l10n_es_vat_book.l10n_es_vat_book_issued_xlsx'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objects):
        book = objects[0]
        merge_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vjustify',
            'fg_color': '#F2F2F2'})
        header_format = workbook.add_format({
            'bold': 1,
            'border': 1,
            'align': 'center',
            'valign': 'vjustify'})
        number_format = workbook.add_format()
        number_format.set_num_format('0.00')

        sheet = workbook.add_worksheet(_('Issued'))

        sheet.merge_range('A1:A2', _('Date Invoice'), merge_format)
        sheet.merge_range('B1:B2', _('Date Operation'), merge_format)
        sheet.merge_range('C1:E1', _('Invoice Identification'), merge_format)
        sheet.merge_range('F1:H1', _('VAT receiver'), merge_format)
        sheet.merge_range('I1:I2', _('Name receiver'), merge_format)
        sheet.merge_range('J1:J2', _('Substitute Invoice'), merge_format)
        sheet.merge_range('K1:K2', _('Operation Key'), merge_format)
        sheet.merge_range('L1:L2', _('Invoice Total'), merge_format)
        sheet.merge_range('M1:M2', _('Invoice Base'), merge_format)
        sheet.merge_range('N1:N2', _('Vat Type'), merge_format)
        sheet.merge_range('O1:O2', _('Issued Amount'), merge_format)
        sheet.merge_range('P1:P2', _('Surcharge Type '), merge_format)
        sheet.merge_range('Q1:Q2', _('Surcharge Amount '), merge_format)
        sheet.merge_range('R1:U1', _('Payment Issued'), merge_format)

        sheet.write('C2', _('Serial'), header_format)
        sheet.write('D2', _('Number'), header_format)
        sheet.write('E2', _('Final Number'), header_format)
        sheet.write('F2', _('Type'), header_format)
        sheet.write('G2', _('Country Code'), header_format)
        sheet.write('H2', _('Identification'), header_format)
        sheet.write('R2', _('Date'), header_format)
        sheet.write('S2', _('Amount'), header_format)
        sheet.write('T2', _('Payment Mode'), header_format)
        sheet.write('U2', _('Payment Mode Identification'), header_format)
        
        sheet.set_column('A:A', 17.77)
        sheet.set_column('B:B', 17.03)
        sheet.set_column('C:C', 14.88)
        sheet.set_column('D:D', 18.32)
        sheet.set_column('E:E', 15.74)
        sheet.set_column('F:F', 9.22)
        sheet.set_column('G:G', 13.95)
        sheet.set_column('H:H', 16.84)
        sheet.set_column('I:I', 28.95)
        sheet.set_column('J:J', 15.31)
        sheet.set_column('K:K', 14.80)
        sheet.set_column('L:L', 12.66)
        sheet.set_column('M:M', 12.66)
        sheet.set_column('N:N', 10.08)
        sheet.set_column('O:O', 12.66)
        sheet.set_column('P:P', 11.56)
        sheet.set_column('Q:Q', 12.66)
        sheet.set_column('R:R', 17.03)
        sheet.set_column('S:S', 12.66)
        sheet.set_column('T:T', 14.80)
        sheet.set_column('U:U', 31.29)
        
        lines = book.issued_line_ids + book.rectification_issued_line_ids
        lines = lines.sorted(key=lambda i: i.invoice_date)
        row = 3
        for line in lines:
            invoice = line.invoice_id
            for tax_line in line.tax_line_ids:
                if tax_line.tax_rate not in [0.5, 1.4, 5.2]:
                    invoice_date = datetime.strptime(
                        line.invoice_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                    sheet.write('A' + str(row), invoice_date)
                    sheet.write('B' + str(row), invoice_date)
                    sheet.write('D' + str(row), invoice.number[0:20])
                    if line.vat_number:
                        if line.vat_number[0:2] == 'ES':
                            sheet.write(
                                'H' + str(row), line.vat_number[2:][0:20])
                        else:
                            if line.vat_number[0:2] in EUROPE:
                                sheet.write('F' + str(row), '02')
                            else:
                                sheet.write('F' + str(row), '04')
                            sheet.write('G' + str(row), line.vat_number[0:2])
                            sheet.write('H' + str(row), line.vat_number[0:20])
                    if line.partner_id:
                        sheet.write('I' + str(row), line.partner_id.name[0:20])
                    if invoice.type == 'out_refund':
                        sheet.write(
                            'L' + str(row),
                            -tax_line.total_amount, number_format)
                        sheet.write(
                            'M' + str(row),
                            -tax_line.base_amount, number_format)
                        sheet.write(
                            'O' + str(row),
                            -tax_line.tax_amount, number_format)
                    else:
                        sheet.write(
                            'L' + str(row),
                            tax_line.total_amount, number_format)
                        sheet.write(
                            'M' + str(row),
                            tax_line.base_amount, number_format)
                        sheet.write(
                            'O' + str(row),
                            tax_line.tax_amount, number_format)
                    sheet.write(
                        'N' + str(row), tax_line.tax_rate, number_format)

                    re_rate = 0
                    if tax_line.tax_rate == 21:
                        re_rate = 5.2
                    if tax_line.tax_rate == 10:
                        re_rate = 1.4
                    if tax_line.tax_rate == 4:
                        re_rate = 0.5
                    re_line = line.tax_line_ids.filtered(
                        lambda r: r.tax_rate == re_rate and \
                        r.base_amount == tax_line.base_amount)
                    if re_line:
                        sheet.write(
                            'P' + str(row), re_rate, number_format)
                        if invoice.type == 'out_refund':
                            sheet.write(
                                'Q' + str(row),
                                -re_line.tax_amount, number_format)
                        else:
                            sheet.write(
                                'Q' + str(row),
                                re_line.tax_amount, number_format) 
                    row += 1
