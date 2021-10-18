# Copyright 2019 Tecnativa - Carlos Dauden
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import fields, models
from odoo.tools import ormcache


def excel_col_number(col_name):
    """Excel column name to number"""
    n = 0
    for c in col_name:
        n = n * 26 + 1 + ord(c) - ord("A")
    return n - 1


class VatNumberXlsx(models.AbstractModel):
    _name = "report.l10n_es_vat_book.l10n_es_vat_book_xlsx"
    _description = "Vat Number Xlsx"
    _inherit = "report.report_xlsx.abstract"

    def format_boe_date(self, date):
        return fields.Datetime.to_datetime(date)

    @ormcache("self.id")
    def _get_undeductible_taxes(self, book):
        line = self.env.ref("l10n_es_vat_book.aeat_vat_book_map_line_p_iva_nd")
        return book.get_taxes_from_templates(line.tax_tmpl_ids)

    def _get_vat_book_map_lines(self, book_type):
        return self.env["aeat.vat.book.map.line"].search(
            [
                ("special_tax_group", "!=", False),
                ("book_type", "=", book_type),
                ("fee_type_xlsx_column", "!=", False),
                ("fee_amount_xlsx_column", "!=", False),
            ]
        )

    def create_issued_sheet(self, workbook, book, draft_export):
        title_format = workbook.add_format(
            {"bold": 1, "border": 1, "align": "center", "valign": "vjustify"}
        )
        header_format = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "align": "center",
                "valign": "vjustify",
                "fg_color": "#F2F2F2",
            }
        )
        subheader_format = workbook.add_format(
            {"bold": 1, "border": 1, "align": "center", "valign": "vjustify"}
        )
        decimal_format = workbook.add_format({"num_format": "0.00"})
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})

        sheet = workbook.add_worksheet("EXPEDIDAS")

        sheet.merge_range("B1:Q1", "LIBRO REGISTRO FACTURAS EXPEDIDAS", title_format)
        sheet.write("A2", "Ejercicio: %s" % book.year)
        sheet.write("A3", "NIF: %s" % book.company_vat)
        sheet.merge_range("A4:D4", "NOMBRE/RAZÓN SOCIAL: %s" % book.company_id.name)

        sheet.merge_range("C6:E6", "Identificación de la Factura", header_format)
        sheet.merge_range("F6:H6", "NIF Destinatario", header_format)

        sheet.merge_range("A6:A7", "Fecha Expedición", header_format)
        sheet.merge_range("B6:B7", "Fecha Operación", header_format)
        sheet.write("C7", "Serie", subheader_format)
        sheet.write("D7", "Número", subheader_format)
        sheet.write("E7", "Número-Final", subheader_format)
        sheet.write("F7", "Tipo", subheader_format)
        sheet.write("G7", "Código País", subheader_format)
        sheet.write("H7", "Identificación", subheader_format)
        sheet.merge_range("I6:I7", "Nombre Destinatario", header_format)
        sheet.merge_range("J6:J7", "Factura Sustitutiva", header_format)
        sheet.merge_range("K6:K7", "Clave de Operación", header_format)
        sheet.merge_range("L6:L7", "Total Factura", header_format)
        sheet.merge_range("M6:M7", "Base Imponible", header_format)
        sheet.merge_range("N6:N7", "Tipo de IVA", header_format)
        sheet.merge_range("O6:O7", "Cuota IVA Repercutida", header_format)
        last_col = "O"
        for line in self._get_vat_book_map_lines("issued"):
            sheet.merge_range(
                "{0}6:{0}7".format(line.fee_type_xlsx_column),
                "Tipo de {}".format(line.name),
                header_format,
            )
            sheet.merge_range(
                "{0}6:{0}7".format(line.fee_amount_xlsx_column),
                "Cuota {}".format(line.name),
                header_format,
            )
            last_col = line.fee_amount_xlsx_column
        next_col = excel_col_number(last_col) + 1
        # Las filas empiezan por 0, por eso se resta 1
        sheet.merge_range(
            5,
            next_col,
            5,
            next_col + 3,
            "Cobro (Operación Criterio de Caja)",
            header_format,
        )
        sheet.write(6, next_col, "Fecha", subheader_format)
        next_col += 1
        sheet.write(6, next_col, "Importe", subheader_format)
        next_col += 1
        sheet.write(6, next_col, "Medio Utilizado", subheader_format)
        next_col += 1
        sheet.write(6, next_col, "Identificación Medio Utilizado", subheader_format)

        sheet.set_column("A:B", 16, date_format)
        sheet.set_column("C:C", 14)
        sheet.set_column("D:D", 17)
        sheet.set_column("E:E", 17)
        sheet.set_column("F:F", 8)
        sheet.set_column("G:G", 12)
        sheet.set_column("H:H", 14)
        sheet.set_column("I:I", 40)
        sheet.set_column("J:J", 16)
        sheet.set_column("K:K", 16)
        sheet.set_column("L:Q", 14, decimal_format)

        next_col = excel_col_number(last_col) + 1
        sheet.set_column(next_col, next_col, 14, date_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14, decimal_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14)
        next_col += 1
        sheet.set_column(next_col, next_col, 30)
        if draft_export:
            next_col += 1
            sheet.write(5, next_col, "Impuesto (Solo borrador)")
            sheet.set_column(next_col, next_col, 50)

        return sheet

    def fill_issued_row_data(
        self, sheet, row, line, tax_line, with_total, draft_export
    ):
        """ Fill issued data """
        # We don't want to fail on empty records, like in the case of PoS
        # cash sales, which dont't have a partner. Just return empty values.
        # Country code will be "ES", as the operations will be made in Spain
        # in all cases.
        country_code, identifier_type, vat_number = (
            line.partner_id and line.partner_id._parse_aeat_vat_info() or ("ES", "", "")
        )
        sheet.write("A" + str(row), self.format_boe_date(line.invoice_date))
        # sheet.write('B' + str(row), self.format_boe_date(line.invoice_date))
        sheet.write("C" + str(row), line.ref[:-20])
        sheet.write("D" + str(row), line.ref[-20:])
        sheet.write("E" + str(row), "")  # Final number
        sheet.write("F" + str(row), identifier_type)
        if country_code != "ES":
            sheet.write("G" + str(row), country_code)
        sheet.write("H" + str(row), vat_number)
        if not vat_number and (
            line.partner_id.aeat_anonymous_cash_customer or not line.partner_id
        ):
            sheet.write("I" + str(row), "Venta anónima")
        else:
            sheet.write("I" + str(row), line.partner_id.name[:40])
        # TODO: Substitute Invoice
        # sheet.write('J' + str(row),
        #             line.invoice_id.refund_invoice_id.number or '')
        sheet.write("K" + str(row), "")  # Operation Key
        if with_total:
            sheet.write("L" + str(row), line.total_amount)
        sheet.write("M" + str(row), tax_line.base_amount)
        sheet.write("N" + str(row), tax_line.tax_id.amount)
        sheet.write("O" + str(row), tax_line.tax_amount)
        if tax_line.special_tax_id:
            map_vals = line.vat_book_id.get_special_taxes_dic()[
                tax_line.special_tax_id.id
            ]
            sheet.write(
                map_vals["fee_type_xlsx_column"] + str(row),
                tax_line.special_tax_id.amount,
            )
            sheet.write(
                map_vals["fee_amount_xlsx_column"] + str(row),
                tax_line.special_tax_amount,
            )
        if draft_export:
            last_column = sheet.dim_colmax
            num_row = row - 1
            sheet.write(num_row, last_column, tax_line.tax_id.name)

    def create_received_sheet(self, workbook, book, draft_export):
        title_format = workbook.add_format(
            {"bold": 1, "border": 1, "align": "center", "valign": "vjustify"}
        )
        header_format = workbook.add_format(
            {
                "bold": 1,
                "border": 1,
                "align": "center",
                "valign": "vjustify",
                "fg_color": "#F2F2F2",
            }
        )
        subheader_format = workbook.add_format(
            {"bold": 1, "border": 1, "align": "center", "valign": "vjustify"}
        )
        decimal_format = workbook.add_format({"num_format": "0.00"})
        date_format = workbook.add_format({"num_format": "dd/mm/yyyy"})

        sheet = workbook.add_worksheet("RECIBIDAS")

        sheet.merge_range("B1:S1", "LIBRO REGISTRO FACTURAS RECIBIDAS", title_format)
        sheet.write("A2", "Ejercicio: %s" % book.year)
        sheet.write("A3", "NIF: %s" % book.company_vat)
        sheet.merge_range("A4:D4", "NOMBRE/RAZÓN SOCIAL: %s" % book.company_id.name)

        sheet.merge_range(
            "C6:D6", "Identificación Factura del Expedidor", header_format
        )
        sheet.merge_range("G6:I6", "NIF Expedidor", header_format)

        sheet.merge_range("A6:A7", "Fecha Expedición", header_format)
        sheet.merge_range("B6:B7", "Fecha Operación", header_format)
        sheet.write("C7", "(Serie-Número)", subheader_format)
        sheet.write("D7", "Número-Final", subheader_format)
        sheet.merge_range("E6:E7", "Número Recepción", header_format)
        sheet.merge_range("F6:F7", "Número Recepción Final", header_format)
        sheet.write("G7", "Tipo", subheader_format)
        sheet.write("H7", "Código País", subheader_format)
        sheet.write("I7", "Identificación", subheader_format)
        sheet.merge_range("J6:J7", "Nombre Expedidor", header_format)
        sheet.merge_range("K6:K7", "Factura Sustitutiva", header_format)
        sheet.merge_range("L6:L7", "Clave de Operación", header_format)
        sheet.merge_range("M6:M7", "Total Factura", header_format)
        sheet.merge_range("N6:N7", "Base Imponible", header_format)
        sheet.merge_range("O6:O7", "Tipo de IVA", header_format)
        sheet.merge_range("P6:P7", "Cuota IVA Soportado", header_format)
        sheet.merge_range("Q6:Q7", "Cuota Deducible", header_format)
        last_col = "Q"
        for line in self._get_vat_book_map_lines("received"):
            sheet.merge_range(
                "{0}6:{0}7".format(line.fee_type_xlsx_column),
                "Tipo de {}".format(line.name),
                header_format,
            )
            sheet.merge_range(
                "{0}6:{0}7".format(line.fee_amount_xlsx_column),
                "Cuota {}".format(line.name),
                header_format,
            )
            last_col = line.fee_amount_xlsx_column
        next_col = excel_col_number(last_col) + 1
        # Las filas empiezan por 0, por eso se resta 1
        sheet.merge_range(
            5,
            next_col,
            5,
            next_col + 3,
            "Pago (Operación Criterio de Caja)",
            header_format,
        )
        sheet.write(6, next_col, "Fecha", subheader_format)
        next_col += 1
        sheet.write(6, next_col, "Importe", subheader_format)
        next_col += 1
        sheet.write(6, next_col, "Medio Utilizado", subheader_format)
        next_col += 1
        sheet.write(6, next_col, "Identificación Medio Utilizado", subheader_format)

        sheet.set_column("A:B", 16, date_format)
        sheet.set_column("C:F", 17)
        sheet.set_column("G:G", 8)
        sheet.set_column("H:H", 12)
        sheet.set_column("I:I", 14)
        sheet.set_column("J:J", 40)
        sheet.set_column("K:K", 16)
        sheet.set_column("L:L", 14)
        sheet.set_column("M:S", 14, decimal_format)
        next_col = excel_col_number(last_col) + 1
        sheet.set_column(next_col, next_col, 14, date_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14, decimal_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14)
        next_col += 1
        sheet.set_column(next_col, next_col, 30)
        if draft_export:
            next_col += 1
            sheet.write(5, next_col, "Impuesto (Solo borrador)")
            sheet.set_column(next_col, next_col, 50)

        return sheet

    def fill_received_row_data(
        self, sheet, row, line, tax_line, with_total, draft_export
    ):
        """ Fill received data """
        date_invoice = line.move_id.date
        # We don't want to fail on empty records, like in the case of PoS
        # cash sales, which dont't have a partner. Just return empty values.
        # Country code will be "ES", as the operations will be made in Spain
        # in all cases.
        country_code, identifier_type, vat_number = (
            line.partner_id and line.partner_id._parse_aeat_vat_info() or ("ES", "", "")
        )
        sheet.write("A" + str(row), self.format_boe_date(line.invoice_date))
        if date_invoice and date_invoice != line.invoice_date:
            sheet.write("B" + str(row), self.format_boe_date(date_invoice))
        sheet.write("C" + str(row), line.external_ref and line.external_ref[:40] or "")
        sheet.write("D" + str(row), "")
        sheet.write("E" + str(row), line.ref[:20])
        sheet.write("F" + str(row), "")
        sheet.write("G" + str(row), identifier_type)
        if country_code != "ES":
            sheet.write("H" + str(row), country_code)
        sheet.write("I" + str(row), vat_number)
        sheet.write("J" + str(row), line.partner_id.name[:40])
        # TODO: Substitute Invoice
        # sheet.write('K' + str(row),
        #             line.invoice_id.refund_invoice_id.number or '')
        sheet.write("L" + str(row), "")  # Operation Key
        if with_total:
            sheet.write("M" + str(row), line.total_amount)
        sheet.write("N" + str(row), tax_line.base_amount)
        sheet.write("O" + str(row), tax_line.tax_id.amount)
        sheet.write("P" + str(row), tax_line.tax_amount)
        if tax_line.tax_id not in self._get_undeductible_taxes(line.vat_book_id):
            sheet.write("Q" + str(row), tax_line.tax_amount)
        if tax_line.special_tax_id:
            map_vals = line.vat_book_id.get_special_taxes_dic()[
                tax_line.special_tax_id.id
            ]
            sheet.write(
                map_vals["fee_type_xlsx_column"] + str(row),
                tax_line.special_tax_id.amount,
            )
            sheet.write(
                map_vals["fee_amount_xlsx_column"] + str(row),
                tax_line.special_tax_amount,
            )
        if draft_export:
            last_column = sheet.dim_colmax
            num_row = row - 1
            sheet.write(num_row, last_column, tax_line.tax_id.name)

    def generate_xlsx_report(self, workbook, data, objects):
        """ Create vat book xlsx in BOE format """

        book = objects[0]
        draft_export = bool(book.state not in ["done", "posted"])

        # Issued
        issued_sheet = self.create_issued_sheet(workbook, book, draft_export)
        lines = book.issued_line_ids + book.rectification_issued_line_ids
        lines = lines.sorted(key=lambda l: (l.invoice_date, l.ref))
        row = 8
        for line in lines:
            with_total = True
            for tax_line in line.tax_line_ids:
                if not tax_line.special_tax_group:
                    # TODO: Payments bucle
                    self.fill_issued_row_data(
                        issued_sheet, row, line, tax_line, with_total, draft_export
                    )
                    with_total = False
                    row += 1

        # Received
        received_sheet = self.create_received_sheet(workbook, book, draft_export)
        lines = book.received_line_ids + book.rectification_received_line_ids
        lines = lines.sorted(key=lambda l: (l.invoice_date, l.ref))
        row = 8
        for line in lines:
            with_total = True
            for tax_line in line.tax_line_ids:
                if not tax_line.special_tax_group:
                    # TODO: Payments bucle
                    self.fill_received_row_data(
                        received_sheet, row, line, tax_line, with_total, draft_export
                    )
                    with_total = False
                    row += 1
