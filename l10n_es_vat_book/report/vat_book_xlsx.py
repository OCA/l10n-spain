# Copyright 2019 Tecnativa - Carlos Dauden
# Copyright 2026 Tecnativa - Eduardo Ezerouali
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

    @ormcache("self.env")
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

        sheet.merge_range("A6:B6", "Autoliquidación", header_format)
        sheet.merge_range("C6:E6", "Actividad", header_format)
        sheet.merge_range("K6:M6", "Identificación de la Factura", header_format)
        sheet.merge_range("N6:P6", "NIF Destinatario", header_format)

        sheet.write("A7", "Ejercicio", subheader_format)
        sheet.write("B7", "Periodo", subheader_format)
        sheet.write("C7", "Código", subheader_format)
        sheet.write("D7", "Tipo", subheader_format)
        sheet.write("E7", "Grupo o Epígrafe del IAE", subheader_format)
        sheet.merge_range("F6:F7", "Tipo de factura", header_format)
        sheet.merge_range("G6:G7", "Concepto de Ingreso", header_format)
        sheet.merge_range("H6:H7", "Ingreso Computable", header_format)
        sheet.merge_range("I6:I7", "Fecha Expedición", header_format)
        sheet.merge_range("J6:J7", "Fecha Operación", header_format)
        sheet.write("K7", "Serie", subheader_format)
        sheet.write("L7", "Número", subheader_format)
        sheet.write("M7", "Número-Final", subheader_format)
        sheet.write("N7", "Tipo", subheader_format)
        sheet.write("O7", "Código País", subheader_format)
        sheet.write("P7", "Identificación", subheader_format)
        sheet.merge_range("Q6:Q7", "Nombre Destinatario", header_format)
        sheet.merge_range("R6:R7", "Clave de Operación", header_format)
        sheet.merge_range("S6:S7", "Calificación de la operación", header_format)
        sheet.merge_range("T6:T7", "Operación Exenta", header_format)
        sheet.merge_range("U6:U7", "Total Factura", header_format)
        sheet.merge_range("V6:V7", "Base Imponible", header_format)
        sheet.merge_range("W6:W7", "Tipo de IVA", header_format)
        sheet.merge_range("X6:X7", "Cuota IVA Repercutida", header_format)
        last_col = "X"
        for line in self._get_vat_book_map_lines("issued"):
            if line.special_tax_group != "irpf":
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
        next_col += 1
        sheet.merge_range(
            5,
            next_col,
            6,
            next_col,
            "Tipo de Retención del IRPF",
            header_format,
        )
        next_col += 1
        sheet.merge_range(
            5,
            next_col,
            6,
            next_col,
            "Importe Retenido del IRPF",
            header_format,
        )

        sheet.set_column("A:G", 14)
        sheet.set_column("H:H", 16, decimal_format)
        sheet.set_column("I:J", 16, date_format)
        sheet.set_column("K:K", 14)
        sheet.set_column("L:L", 17)
        sheet.set_column("M:M", 17)
        sheet.set_column("N:N", 8)
        sheet.set_column("O:O", 12)
        sheet.set_column("P:P", 14)
        sheet.set_column("Q:Q", 40)
        sheet.set_column("R:T", 16)
        sheet.set_column("U:Z", 14, decimal_format)

        next_col = excel_col_number(last_col) + 1
        sheet.set_column(next_col, next_col, 14, date_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14, decimal_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14)
        next_col += 1
        sheet.set_column(next_col, next_col, 30)
        next_col += 1
        sheet.set_column(next_col, next_col, 16)
        next_col += 1
        sheet.set_column(next_col, next_col, 16)

        if draft_export:
            next_col += 1
            sheet.write(5, next_col, "Impuesto (Solo borrador)")
            sheet.set_column(next_col, next_col, 50)

        return sheet

    def fill_issued_row_data(
        self, sheet, row, line, tax_line, with_total, draft_export
    ):
        """Fill issued data"""
        # We don't want to fail on empty records, like in the case of PoS
        # cash sales, which dont't have a partner. Just return empty values.
        # Country code will be "ES", as the operations will be made in Spain
        # in all cases.
        country_code, identifier_type, vat_number = (
            line.partner_id and line.partner_id._parse_aeat_vat_info() or ("ES", "", "")
        )
        sheet.write("A" + str(row), str(line.vat_book_id.year))
        sheet.write("B" + str(row), str(line.vat_book_id.period_type))
        sheet.write("I" + str(row), self.format_boe_date(line.invoice_date))
        # sheet.write('J' + str(row), self.format_boe_date(line.invoice_date))
        sheet.write("K" + str(row), line.ref[:-20])
        sheet.write("L" + str(row), line.ref[-20:])
        sheet.write("M" + str(row), "")  # Final number
        sheet.write("N" + str(row), identifier_type)
        if country_code != "ES":
            sheet.write("O" + str(row), country_code)
        sheet.write("P" + str(row), vat_number)
        if not vat_number and (
            line.partner_id.aeat_anonymous_cash_customer or not line.partner_id
        ):
            sheet.write("Q" + str(row), "Venta anónima")
        else:
            sheet.write("Q" + str(row), (line.partner_id.name or "")[:40])
        sheet.write("R" + str(row), "")  # Operation Key
        if with_total:
            sheet.write("U" + str(row), line.total_amount)
        sheet.write("V" + str(row), tax_line.base_amount)
        sheet.write("W" + str(row), tax_line.tax_id.amount)
        sheet.write("X" + str(row), tax_line.tax_amount)
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

        sheet.merge_range("A6:B6", "Autoliquidación", header_format)
        sheet.merge_range("C6:E6", "Actividad", header_format)
        sheet.merge_range(
            "K6:L6", "Identificación Factura del Expedidor", header_format
        )
        sheet.merge_range("P6:R6", "NIF Expedidor", header_format)
        sheet.merge_range("X6:Y6", "Periodo Deducción", header_format)

        sheet.write("A7", "Ejercicio", subheader_format)
        sheet.write("B7", "Periodo", subheader_format)
        sheet.write("C7", "Código", subheader_format)
        sheet.write("D7", "Tipo", subheader_format)
        sheet.write("E7", "Grupo o Epígrafe del IAE", subheader_format)
        sheet.merge_range("F6:F7", "Tipo de factura", header_format)
        sheet.merge_range("G6:G7", "Concepto de Gasto", header_format)
        sheet.merge_range("H6:H7", "Gasto Deducible", header_format)
        sheet.merge_range("I6:I7", "Fecha Expedición", header_format)
        sheet.merge_range("J6:J7", "Fecha Operación", header_format)
        sheet.write("K7", "(Serie-Número)", subheader_format)
        sheet.write("L7", "Número-Final", subheader_format)
        sheet.merge_range("M6:M7", "Fecha Recepción", header_format)
        sheet.merge_range("N6:N7", "Número Recepción", header_format)
        sheet.merge_range("O6:O7", "Número Recepción Final", header_format)
        sheet.write("P7", "Tipo", subheader_format)
        sheet.write("Q7", "Código País", subheader_format)
        sheet.write("R7", "Identificación", subheader_format)
        sheet.merge_range("S6:S7", "Nombre Expedidor", header_format)
        sheet.merge_range("T6:T7", "Clave de Operación", header_format)
        sheet.merge_range("U6:U7", "Bien de Inversión", header_format)
        sheet.merge_range("V6:V7", "Inversión del Sujeto Pasivo", header_format)
        sheet.merge_range("W6:W7", "Deducible en Periodo Posterior", header_format)
        sheet.write("X7", "Ejercicio", header_format)
        sheet.write("Y7", "Periodo", header_format)
        sheet.merge_range("Z6:Z7", "Total Factura", header_format)
        sheet.merge_range("AA6:AA7", "Base Imponible", header_format)
        sheet.merge_range("AB6:AB7", "Tipo de IVA", header_format)
        sheet.merge_range("AC6:AC7", "Cuota IVA Soportado", header_format)
        sheet.merge_range("AD6:AD7", "Cuota Deducible", header_format)
        last_col = "AD"
        for line in self._get_vat_book_map_lines("received"):
            if line.special_tax_group != "irpf":
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
        next_col += 1
        sheet.merge_range(
            5,
            next_col,
            6,
            next_col,
            "Tipo de Retención del IRPF",
            header_format,
        )
        next_col += 1
        sheet.merge_range(
            5,
            next_col,
            6,
            next_col,
            "Importe Retenido del IRPF",
            header_format,
        )
        next_col += 1
        sheet.merge_range(
            5,
            next_col,
            6,
            next_col,
            "Registro Acuerdo Facturación",
            header_format,
        )

        sheet.set_column("A:G", 14)
        sheet.set_column("H:H", 16, decimal_format)
        sheet.set_column("I:J", 16, date_format)
        sheet.set_column("K:O", 17)
        sheet.set_column("P:P", 8)
        sheet.set_column("Q:Q", 12)
        sheet.set_column("R:R", 14)
        sheet.set_column("S:S", 40)
        sheet.set_column("T:Y", 16)
        sheet.set_column("Z:AF", 14, decimal_format)
        next_col = excel_col_number(last_col) + 1
        sheet.set_column(next_col, next_col, 14, date_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14, decimal_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14)
        next_col += 1
        sheet.set_column(next_col, next_col, 30)
        next_col += 1
        sheet.set_column(next_col, next_col, 14, decimal_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 14, decimal_format)
        next_col += 1
        sheet.set_column(next_col, next_col, 16)

        if draft_export:
            next_col += 1
            sheet.write(5, next_col, "Impuesto (Solo borrador)")
            sheet.set_column(next_col, next_col, 50)

        return sheet

    def fill_received_row_data(
        self, sheet, row, line, tax_line, with_total, draft_export
    ):
        """Fill received data"""
        date_invoice = line.move_id.date
        # We don't want to fail on empty records, like in the case of PoS
        # cash sales, which dont't have a partner. Just return empty values.
        # Country code will be "ES", as the operations will be made in Spain
        # in all cases.
        country_code, identifier_type, vat_number = (
            line.partner_id and line.partner_id._parse_aeat_vat_info() or ("ES", "", "")
        )
        sheet.write("A" + str(row), str(line.vat_book_id.year))
        sheet.write("B" + str(row), str(line.vat_book_id.period_type))
        sheet.write("I" + str(row), self.format_boe_date(line.invoice_date))
        if date_invoice and date_invoice != line.invoice_date:
            sheet.write("J" + str(row), self.format_boe_date(date_invoice))
        sheet.write("K" + str(row), (line.external_ref or "")[:40])
        sheet.write("L" + str(row), "")
        sheet.write("N" + str(row), line.ref[:20])
        sheet.write("O" + str(row), "")
        sheet.write("P" + str(row), identifier_type)
        if country_code != "ES":
            sheet.write("Q" + str(row), country_code)
        sheet.write("R" + str(row), vat_number)
        sheet.write("S" + str(row), (line.partner_id.name or "")[:40])
        sheet.write("T" + str(row), "")  # Operation Key
        sheet.write("X" + str(row), line.move_id.date.year)
        sheet.write("Y" + str(row), line._get_settlement_period())
        if with_total:
            sheet.write("Z" + str(row), line.total_amount)
        sheet.write("AA" + str(row), tax_line.base_amount)
        sheet.write("AB" + str(row), tax_line.tax_id.amount)
        sheet.write("AC" + str(row), tax_line.tax_amount)
        if tax_line.tax_id not in self._get_undeductible_taxes(line.vat_book_id):
            sheet.write("AD" + str(row), tax_line.deductible_amount)
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
        """Create vat book xlsx in BOE format"""

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
