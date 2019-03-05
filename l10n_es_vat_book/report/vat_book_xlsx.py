# -*- coding: utf-8 -*-
# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object
from datetime import datetime
from odoo import fields, _
from odoo.report import report_sxw


class VatNumberXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, objects):
        book = objects[0]

        def _get_gen_type(invoice):
            """Make a choice for general invoice type

            Returns:
                int: 1 (National), 2 (Intracom), 3 (Export)
            """
            partner_ident = invoice.fiscal_position_id.partner_identification_type
            if partner_ident:
                res = int(partner_ident)
            elif invoice.fiscal_position_id.name == u'Régimen Intracomunitario':
                res = 2
            elif (invoice.fiscal_position_id.name ==
                  u'Régimen Extracomunitario / Canarias, Ceuta y Melilla'):
                res = 3
            else:
                res = 1
            return res

        def _get_identifier(invoice, country_code):
            gen_type = _get_gen_type(invoice)
            if invoice.partner_id.simplified_invoice:
                return ""
            # Limpiar alfanum
            if invoice.partner_id.vat:
                vat = ''.join(
                    e for e in invoice.partner_id.vat if e.isalnum()
                ).upper()
            else:
                vat = 'NO_DISPONIBLE'
            if gen_type == 1:
                if country_code != 'ES':
                    id_type = '06' if vat == 'NO_DISPONIBLE' else '04'
                    return id_type
                else:
                    return ""
            elif gen_type == 2:
                return "02"
            elif gen_type == 3 and country_code != 'ES':
                id_type = '06' if vat == 'NO_DISPONIBLE' else '04'
                return id_type
            elif gen_type == 3:
                return ""

        def fill_table_received(lines, vatbook=False):
            sheet = workbook.add_worksheet(_(u"EXPEDIDAS"))
            cell_main_title = workbook.add_format({
                "font_size": 12,
                "bold": True,
                "align": "center",
            })
            sheet.merge_range(
                "B1:M1",
                _(u"LIBRO REGISTRO FACTURAS EXPEDIDAS"),
                cell_main_title,
            )
            cell_title = workbook.add_format({
                "font_size": 10,
                "bold": True,
            })
            sheet.write(1, 0, _(u"Ejercicio: %s" % vatbook.year), cell_title)
            vat = vatbook.company_id.vat and vatbook.company_id.vat[2:] or ""
            sheet.write(2, 0, _(u"NIF: %s") % vat, cell_title)
            sheet.write(
                3, 0,
                _(u"NOMBRE O RAZÓN SOCIAL: %s" % vatbook.company_id.name),
                cell_title
            )
            cell_table = workbook.add_format({
                "font_size": 10,
                "bold": True,
            })
            cell_sub_table = workbook.add_format({
                "font_size": 10,
                "bold": True,
            })
            cell_table.set_align("center")
            cell_table.set_align("vcenter")
            cell_table.set_text_wrap()
            cell_table.set_bg_color("#F2F2F2")
            cell_table.set_border()
            cell_sub_table.set_border()
            sheet.merge_range(
                "A6:A7",
                _(u"Fecha Expedición"),
                cell_table,
            )
            sheet.merge_range(
                "B6:B7",
                _(u"Fecha Operación"),
                cell_table,
            )
            sheet.write(6, 2, _(u"Serie"), cell_sub_table)
            sheet.write(6, 3, _(u"Número"), cell_sub_table)
            sheet.merge_range(
                "C6:D6",
                _(u"Identificación de la Factura"),
                cell_table,
            )
            sheet.merge_range(
                "E6:G6",
                _(u"NIF Destinatario"),
                cell_table,
            )
            sheet.write(6, 4, _(u"Código País"), cell_sub_table)
            sheet.write(6, 5, _(u"Tipo"), cell_sub_table)
            sheet.write(6, 6, _(u"Identificación"), cell_sub_table)
            sheet.merge_range(
                "H6:H7",
                _(u"Nombre Destinatario"),
                cell_table,
            )
            sheet.merge_range(
                "I6:I7",
                _(u"Base Imponible"),
                cell_table,
            )
            sheet.merge_range(
                "J6:J7",
                _(u"Tipo de IVA"),
                cell_table,
            )
            sheet.merge_range(
                "K6:K7",
                _(u"Cuota IVA Repercutida"),
                cell_table,
            )
            sheet.merge_range(
                "L6:L7",
                _(u"Tipo de Recargo Eq."),
                cell_table,
            )
            sheet.merge_range(
                "M6:M7",
                _(u"Cuota Recargo Eq."),
                cell_table,
            )
            sheet.merge_range(
                "N6:N7",
                _(u"Total Factura"),
                cell_table,
            )
            sheet.merge_range(
                "O6:O7",
                _(u"Clave de Operación"),
                cell_table,
            )
            sheet.merge_range(
                "P6:S6",
                _(u"Cobro"),
                cell_table,
            )
            sheet.write(6, 15, _(u"Fecha"), cell_sub_table)
            sheet.write(6, 16, _(u"Importe"), cell_sub_table)
            sheet.write(6, 17, _(u"Medio Utilizado"), cell_sub_table)
            sheet.write(
                6, 18, _(u"Identificación Medio Utilizado"), cell_sub_table
            )
            cell_table_center = workbook.add_format({
                "font_size": 11,
                "align": "center",
            })
            cell_table_right = workbook.add_format({
                "font_size": 11,
                "align": "right",
            })
            cell_table_left = workbook.add_format({
                "font_size": 11,
                "align": "left",
            })
            row = 7
            taxes = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_RE"
            ).tax_ids.ids
            taxes2 = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_SFRETENCIONES"
            ).tax_ids.ids
            obj_tax = self.env["account.fiscal.position.tax"]
            for lin in lines:
                for line in lin.tax_line_ids:
                    tax_dest_id = False
                    if line.tax_id.id in taxes+taxes2:
                        continue
                    elif(line.tax_id.id in lin.invoice_id.fiscal_position_id.
                            tax_ids.mapped("tax_src_id").ids):
                        tax_dest_id = obj_tax.search([
                            ("position_id", "=",
                             lin.invoice_id.fiscal_position_id.id),
                            ("tax_src_id", "=", line.tax_id.id),
                            ("tax_dest_id", "in", taxes)
                        ]).tax_dest_id
                        tax_dest_id = lin.tax_line_ids.filtered(
                            lambda r: r.tax_id == tax_dest_id
                        )
                    col = 0
                    # Fecha Expedición
                    date_invoice = fields.Date.from_string(
                            lin.invoice_id.date_invoice).strftime("%d-%m-%Y")
                    sheet.write(
                        row, col,
                        date_invoice,
                        cell_table_center,
                    )
                    col += 1
                    # Fecha Operación
                    sheet.write(
                        row, col,
                        date_invoice,
                        cell_table_right,
                    )
                    col += 1
                    # Serie
                    col += 1
                    # Número
                    sheet.write(
                        row, col, lin.invoice_id.number[:20], cell_table_right,
                    )
                    col += 1
                    # Código País
                    country_code = (
                            lin.invoice_id.partner_id.country_id.code or
                            (lin.invoice_id.partner_id.vat or "")[:2]
                    ).upper()
                    sheet.write(
                        row, col, country_code, cell_table_left,
                    )
                    col += 1
                    # Tipo
                    tipo = _get_identifier(lin.invoice_id, country_code)
                    sheet.write(row, col, tipo, cell_table_left)
                    col += 1
                    # Identificación
                    if country_code != "ES":
                        vat = lin.invoice_id.partner_id.vat or ""
                        vat = vat[:20]
                    else:
                        vat = lin.invoice_id.partner_id.vat[2:]
                    sheet.write(row, col, vat, cell_table_left)
                    col += 1
                    # Nombre destinatario
                    if lin.invoice_id.partner_id.simplified_invoice:
                        ndest = "VENTA POR CAJA"
                    else:
                        ndest = lin.invoice_id.partner_id.name[:40]
                    sheet.write(row, col, ndest, cell_table_left)
                    col += 1
                    # Base imponible
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(
                            line.base_amount).replace(".", ",")[:13],
                        cell_table_right,
                    )
                    col += 1
                    # Tipo de IVA
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(line.tax_id.amount).replace(
                            ".", ",")[:5], cell_table_right
                    )
                    col += 1
                    # Cuota IVA repercutida
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(line.tax_amount).replace(
                            ".", ",")[:13], cell_table_right
                    )
                    col += 1
                    # Tipo de recargo eq.
                    if tax_dest_id:
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(
                                tax_dest_id.tax_id.amount).replace(
                                ".", ","
                            )[:5], cell_table_right)
                    col += 1
                    # Cuota de recargo eq.
                    if tax_dest_id:
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(tax_dest_id.tax_amount).replace(
                                ".", ",")[:13], cell_table_right
                        )
                    col += 1
                    # Total factura
                    tax1 = lin.mapped("tax_line_ids.tax_id").filtered(
                        lambda r: r.id not in taxes+taxes2
                    ).ids
                    tax1 = lin.mapped("tax_line_ids").filtered(
                        lambda r: r.tax_id.id in tax1
                    )
                    tax2 = lin.mapped("tax_line_ids.tax_id").filtered(
                        lambda r: r.id in taxes
                    ).ids
                    tax2 = lin.mapped("tax_line_ids").filtered(
                        lambda r: r.tax_id.id in tax2
                    )
                    total = sum(x.total_amount for x in tax1)
                    total += sum(x.tax_amount for x in tax2)
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(total).replace(
                            ".", ",")[:13], cell_table_right
                    )
                    col += 1
                    row += 1

        def fill_table_issued(lines, vatbook=False):
            sheet = workbook.add_worksheet(_(u"RECIBIDAS"))
            cell_main_title = workbook.add_format({
                "font_size": 12,
                "bold": True,
                "align": "center",
            })
            sheet.merge_range(
                "B1:M1",
                _(u"LIBRO REGISTRO FACTURAS RECIBIDAS"),
                cell_main_title,
            )
            cell_title = workbook.add_format({
                "font_size": 10,
                "bold": True,
            })
            sheet.write(1, 0, _(u"Ejercicio: %s" % vatbook.year), cell_title)
            vat = vatbook.company_id.vat and vatbook.company_id.vat[2:] or ""
            sheet.write(2, 0, _(u"NIF: %s") % vat, cell_title)
            sheet.write(
                3, 0,
                _(u"NOMBRE O RAZÓN SOCIAL: %s" % vatbook.company_id.name),
                cell_title
            )
            cell_table = workbook.add_format({
                "font_size": 10,
                "bold": True,
            })
            cell_sub_table = workbook.add_format({
                "font_size": 10,
                "bold": True,
            })
            cell_table.set_align("center")
            cell_table.set_align("vcenter")
            cell_table.set_text_wrap()
            cell_table.set_bg_color("#F2F2F2")
            cell_table.set_border()
            cell_sub_table.set_border()
            sheet.merge_range(
                "A6:A7",
                _(u"Fecha Expedición"),
                cell_table,
            )
            sheet.merge_range(
                "B6:B7",
                _(u"Fecha Operación"),
                cell_table,
            )
            sheet.write(6, 2, _(u"Serie"), cell_sub_table)
            sheet.write(6, 3, _(u"Número"), cell_sub_table)
            sheet.merge_range(
                "C6:D6",
                _(u"Identificación Factura del Expedidor"),
                cell_table,
            )
            sheet.merge_range(
                "E6:E7",
                _(u"Número Recepción"),
                cell_table,
            )
            sheet.merge_range(
                "F6:H6",
                _(u"NIF Expedidor"),
                cell_table,
            )
            sheet.write(6, 5, _(u"Código País"), cell_sub_table)
            sheet.write(6, 6, _(u"Tipo"), cell_sub_table)
            sheet.write(6, 7, _(u"Identificación"), cell_sub_table)
            sheet.merge_range(
                "I6:I7",
                _(u"Nombre Expedidor"),
                cell_table,
            )
            sheet.merge_range(
                "J6:J7",
                _(u"Base Imponible"),
                cell_table,
            )
            sheet.merge_range(
                "K6:K7",
                _(u"Tipo de IVA"),
                cell_table,
            )
            sheet.merge_range(
                "L6:L7",
                _(u"Cuota IVA Soportador"),
                cell_table,
            )
            sheet.merge_range(
                "M6:M7",
                _(u"Cuota Deducible"),
                cell_table,
            )
            sheet.merge_range(
                "N6:N7",
                _(u"Total Factura"),
                cell_table,
            )
            sheet.merge_range(
                "O6:O7",
                _(u"Clave de Operación"),
                cell_table,
            )
            sheet.merge_range(
                "P6:S6",
                _(u"Pago"),
                cell_table,
            )
            sheet.write(6, 16, _(u"Fecha"), cell_sub_table)
            sheet.write(6, 17, _(u"Importe"), cell_sub_table)
            sheet.write(6, 18, _(u"Medio Utilizado"), cell_sub_table)
            sheet.write(
                6, 19, _(u"Identificación Medio Utilizado"), cell_sub_table
            )
            cell_table_center = workbook.add_format({
                "font_size": 11,
                "align": "center",
            })
            cell_table_right = workbook.add_format({
                "font_size": 11,
                "align": "right",
            })
            cell_table_left = workbook.add_format({
                "font_size": 11,
                "align": "left",
            })
            row = 7
            taxes = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_RE"
            ).tax_ids.ids
            taxes2 = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_SFRETENCIONES"
            ).tax_ids.ids
            taxes3 = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_SFRND"
            ).tax_ids.ids
            obj_tax = self.env["account.fiscal.position.tax"]
            for lin in lines:
                for line in lin.tax_line_ids:
                    tax_dest_id = False
                    if line.tax_id.id in taxes + taxes2:
                        continue
                    elif (line.tax_id.id in lin.invoice_id.fiscal_position_id.
                            tax_ids.mapped("tax_src_id").ids):
                        tax_dest_id = obj_tax.search([
                            ("position_id", "=",
                             lin.invoice_id.fiscal_position_id.id),
                            ("tax_src_id", "=", line.tax_id.id),
                            ("tax_dest_id", "in", taxes)
                        ]).tax_dest_id
                        tax_dest_id = lin.tax_line_ids.filtered(
                            lambda r: r.tax_id == tax_dest_id
                        )
                    col = 0
                    # Fecha Expedición
                    date_invoice = fields.Date.from_string(
                        lin.invoice_id.date_invoice).strftime("%d-%m-%Y")
                    sheet.write(
                        row, col,
                        date_invoice,
                        cell_table_center,
                    )
                    col += 1
                    # Fecha Operación
                    if lin.invoice_id.move_id.date != \
                            lin.invoice_id.date_invoice:
                        sheet.write(
                            row, col,
                            fields.Date.from_string(
                                lin.invoice_id.move_id.date.strftime("%d-%m-%Y")
                            ),
                            cell_table_right,
                        )
                    col += 1
                    # Serie
                    col += 1
                    # Número
                    sheet.write(
                        row, col, lin.invoice_id.reference[:20], cell_table_right,
                    )
                    col += 1
                    # Número recepción
                    # sheet.write(
                    #     row, col, lin.invoice_id.number[:20], cell_table_right,
                    # )
                    col += 1
                    # Código País
                    country_code = (
                            lin.invoice_id.partner_id.country_id.code or
                            (lin.invoice_id.partner_id.vat or "")[:2]
                    ).upper()
                    sheet.write(
                        row, col, country_code, cell_table_left,
                    )
                    col += 1
                    # Tipo
                    tipo = _get_identifier(lin.invoice_id, country_code)
                    sheet.write(row, col, tipo, cell_table_left)
                    col += 1
                    # Identificación
                    if country_code != "ES":
                        vat = lin.invoice_id.partner_id.vat or ""
                        vat = vat[:20]
                    else:
                        vat = lin.invoice_id.partner_id.vat[2:]
                    sheet.write(row, col, vat, cell_table_left)
                    col += 1
                    # Nombre expendidor
                    supplier = lin.invoice_id.partner_id.name[:40]
                    sheet.write(row, col, supplier, cell_table_left)
                    col += 1
                    # Base imponible
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(
                            line.base_amount).replace(".", ",")[:13],
                        cell_table_right,
                    )
                    col += 1
                    # Tipo de IVA
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(line.tax_id.amount).replace(
                            ".", ",")[:5], cell_table_right
                    )
                    col += 1
                    # Cuota IVA soportado
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(line.tax_amount).replace(
                            ".", ",")[:13], cell_table_right
                    )
                    col += 1
                    # Cuota Deducible
                    if line.tax_id.id not in taxes3:
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(line.tax_amount).replace(
                                ".", ",")[:13], cell_table_right
                        )
                    col += 1
                    # Total factura
                    if tax_dest_id:
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(
                                tax_dest_id.tax_id.amount).replace(
                                ".", ","
                            )[:5], cell_table_right)
                    col += 1
                    # Cuota de recargo eq.
                    if tax_dest_id:
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(tax_dest_id.tax_amount).replace(
                                ".", ",")[:13], cell_table_right
                        )
                    col += 1
                    # Total factura
                    tax1 = lin.mapped("tax_line_ids.tax_id").filtered(
                        lambda r: r.id not in taxes + taxes2
                    ).ids
                    tax1 = lin.mapped("tax_line_ids").filtered(
                        lambda r: r.tax_id.id in tax1
                    )
                    tax2 = lin.mapped("tax_line_ids.tax_id").filtered(
                        lambda r: r.id in taxes
                    ).ids
                    tax2 = lin.mapped("tax_line_ids").filtered(
                        lambda r: r.tax_id.id in tax2
                    )
                    total = sum(x.total_amount for x in tax1)
                    total += sum(x.tax_amount for x in tax2)
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(total).replace(
                            ".", ",")[:13], cell_table_right
                    )
                    col += 1
                    row += 1


        if book.issued_line_ids or book.rectification_issued_line_ids:
            lines = book.issued_line_ids + book.rectification_issued_line_ids
            fill_table_received(lines, book)
        else:
            lines = book.received_line_ids + \
                    book.rectification_received_line_ids
            fill_table_issued(lines, book)


if ReportXlsx != object:
    VatNumberXlsx(
        'report.l10n_es_vat_book.l10n_es_vat_book_xlsx',
        'l10n.es.vat.book', parser=report_sxw.rml_parse,
    )
