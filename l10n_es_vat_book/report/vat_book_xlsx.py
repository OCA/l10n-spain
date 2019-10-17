# -*- coding: utf-8 -*-
# Copyright 2018 Luis M. Ontalba <luismaront@gmail.com>
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
# https://www.agenciatributaria.es/AEAT.desarrolladores/Desarrolladores/_menu_/Documentacion/IVA/Modelo_303/Modelo_303.html

try:
    from odoo.addons.report_xlsx.report.report_xlsx import ReportXlsx
except ImportError:
    ReportXlsx = object
from odoo import fields, _
from odoo.report import report_sxw
from odoo.exceptions import UserError


class VatNumberXlsx(ReportXlsx):
    def generate_xlsx_report(self, workbook, data, objects):
        book = objects[0]

        def _get_gen_type(identifier):
            """Make a choice for general invoice type

            Returns:
                int: 1 (National), 2 (Intracom), 3 (Export)
            """
            if identifier._name == "account.invoice":
                identifier = identifier.fiscal_position_id
            else:
                identifier = identifier.property_account_position_id
            partner_ident = \
                identifier.partner_identification_type
            if partner_ident:
                res = int(partner_ident)
            elif identifier.name == \
                    u'Régimen Intracomunitario':
                res = 2
            elif (identifier.name ==
                  u'Régimen Extracomunitario / Canarias, Ceuta y Melilla'):
                res = 3
            else:
                res = 1
            return res

        def _get_identifier(identifier, country_code):
            gen_type = _get_gen_type(identifier)
            vat = False
            if identifier._name != "account.invoice":
                if identifier.simplified_invoice:
                    return ""
                else:
                    vat = identifier.vat
            # Limpiar alfanum
            vat = vat or identifier.partner_id.vat
            if vat:
                vat = ''.join(e for e in vat if e.isalnum()).upper()
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

        def fill_table_issued(lines, vatbook=False):
            sheet = workbook.add_worksheet(_(u"EXPEDIDAS"))
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
            cell_sub_table.set_align("center")
            cell_sub_table.set_align("vcenter")
            cell_sub_table.set_text_wrap()
            cell_sub_table.set_border()
            sheet.merge_range(
                "A1:A2",
                _(u"Fecha Expedición"),
                cell_table,
            )
            sheet.merge_range(
                "B1:B2",
                _(u"Fecha Operación"),
                cell_table,
            )
            sheet.merge_range(
                "C1:E1",
                _(u"Identificación de la Factura"),
                cell_table,
            )
            sheet.write(1, 2, _(u"Serie"), cell_sub_table)
            sheet.write(1, 3, _(u"Número"), cell_sub_table)
            sheet.write(1, 4, _(u"Número-Final"), cell_sub_table)
            sheet.merge_range(
                "F1:H1",
                _(u"NIF Destinatario"),
                cell_table,
            )
            sheet.write(1, 5, _(u"Tipo"), cell_sub_table)
            sheet.write(1, 6, _(u"Código País"), cell_sub_table)
            sheet.write(1, 7, _(u"Identificación"), cell_sub_table)
            sheet.merge_range(
                "I1:I2",
                _(u"Nombre Destinatario"),
                cell_table,
            )
            sheet.merge_range(
                "J1:J2",
                _(u"Factura Sustitutiva"),
                cell_table,
            )
            sheet.merge_range(
                "K1:K2",
                _(u"Clave de Operación"),
                cell_table,
            )
            sheet.merge_range(
                "L1:L2",
                _(u"Total Factura"),
                cell_table,
            )
            sheet.merge_range(
                "M1:M2",
                _(u"Base Imponible"),
                cell_table,
            )
            sheet.merge_range(
                "N1:N2",
                _(u"Tipo de IVA"),
                cell_table,
            )
            sheet.merge_range(
                "O1:O2",
                _(u"Cuota IVA Repercutida"),
                cell_table,
            )
            sheet.merge_range(
                "P1:P2",
                _(u"Tipo de Recargo Eq."),
                cell_table,
            )
            sheet.merge_range(
                "Q1:Q2",
                _(u"Cuota Recargo Eq."),
                cell_table,
            )
            sheet.merge_range(
                "R1:U1",
                _(u"Cobro"),
                cell_table,
            )
            sheet.write(1, 17, _(u"Fecha"), cell_sub_table)
            sheet.write(1, 18, _(u"Importe"), cell_sub_table)
            sheet.write(1, 19, _(u"Medio Utilizado"), cell_sub_table)
            sheet.write(
                1, 20, _(u"Identificación Medio Utilizado"), cell_sub_table
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
            row = 2
            taxes = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_RE"
            ).tax_ids.ids
            taxes2 = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_SFRETENCIONES"
            ).tax_ids.ids
            obj_tax = self.env["account.fiscal.position.tax"]
            for lin in lines:
                fiscal_pos = lin.invoice_id.fiscal_position_id or \
                    lin.partner_id.property_account_position_id
                if not fiscal_pos:
                    raise UserError(_(
                        "Partner %s haven't fiscal position"
                    ) % lin.partner_id.name)
                for line in list(
                        set(lin.mapped("tax_line_ids.tax_id.amount"))):
                    tline = lin.tax_line_ids.filtered(
                        lambda r: r.tax_id.amount == line)[0]
                    lines_all = lin.tax_line_ids.filtered(
                        lambda r: r.tax_id.amount == line)
                    line = tline
                    tax_dest_id = False
                    if line.tax_id.id in taxes + taxes2:
                        continue
                    elif (line.tax_id.id in fiscal_pos.
                            tax_ids.mapped("tax_src_id").ids):
                        tax_dest_id = obj_tax.search([
                            ("position_id", "=", fiscal_pos.id),
                            ("tax_src_id", "=", line.tax_id.id),
                            ("tax_dest_id", "in", taxes)
                        ]).tax_dest_id
                        tax_dest_id = lin.tax_line_ids.filtered(
                            lambda r: r.tax_id == tax_dest_id
                        )
                    col = 0
                    partner = lin.partner_id
                    country_code = (
                        partner.country_id.code or (partner.vat or "")[:2]
                    ).upper()
                    # Fecha Expedición
                    date_invoice = (
                        lin.invoice_id.date_invoice or lin.move_id.date)
                    date_invoice = fields.Date.from_string(
                        date_invoice).strftime("%d/%m/%Y")
                    sheet.write(
                        row, col,
                        date_invoice,
                        cell_table_center,
                    )
                    col += 1
                    # Fecha Operación
                    col += 1
                    # Serie
                    col += 1
                    # Número
                    sheet.write(
                        row, col, (lin.invoice_id.number or lin.move_id.ref)[
                            :20], cell_table_center,
                    )
                    col += 1
                    # Número final
                    col += 1
                    # Tipo
                    identifier = lin.invoice_id or lin.partner_id
                    tipo = _get_identifier(identifier, country_code)[:2]
                    sheet.write(row, col, tipo, cell_table_center)
                    col += 1
                    # Código País
                    sheet.write(
                        row, col, country_code, cell_table_center,
                    )
                    col += 1
                    # Identificación
                    if country_code != "ES":
                        vat = partner.vat or ""
                        vat = vat[:20]
                    else:
                        vat = partner.vat[2:]
                    sheet.write(row, col, vat, cell_table_left)
                    col += 1
                    # Nombre destinatario
                    if partner.simplified_invoice:
                        ndest = "VENTA POR CAJA"
                    else:
                        ndest = partner.name[:40]
                    sheet.write(row, col, ndest, cell_table_left)
                    col += 1
                    # Factura sustitiva
                    col += 1
                    # Clave de operación
                    col += 1
                    # Total factura
                    subjected_base = sum(lines_all.mapped('base_amount'))
                    cuota_rep = sum(x.tax_amount for x in lines_all)
                    cuota_rec_eq = (tax_dest_id and tax_dest_id.tax_amount) or 0
                    total_factura = base_imponible + cuota_rep + cuota_rec_eq
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(total_factura).replace(
                            ".", ",")[:13], cell_table_right
                    )
                    col += 1
                    # Base imponible
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(base_imponible).replace(
                            ".", ",")[:13],
                        cell_table_right,
                    )
                    col += 1
                    # Tipo de IVA
                    if line.tax_id.amount_type not in (
                            'fixed', 'percent', 'division'):
                        sheet.write(
                            row, col, 0, cell_table_right
                        )
                    else:
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(line.tax_id.amount).replace(
                                ".", ",")[:5], cell_table_right
                        )
                    col += 1
                    # Cuota IVA repercutida
                    sheet.write(
                        row, col,
                        "{0:.2f}".format(cuota_rep).replace(
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
                    row += 1

        def fill_table_received(lines, vatbook=False):
            sheet = workbook.add_worksheet(_(u"RECIBIDAS"))
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
            cell_sub_table.set_align("center")
            cell_sub_table.set_align("vcenter")
            cell_sub_table.set_text_wrap()
            cell_table.set_border()
            sheet.merge_range(
                "A1:A2",
                _(u"Fecha Expedición"),
                cell_table,
            )
            sheet.merge_range(
                "B1:B2",
                _(u"Fecha Operación"),
                cell_table,
            )
            sheet.merge_range(
                "C1:D1",
                _(u"Identificación Factura del Expedidor"),
                cell_table,
            )
            sheet.write(1, 2, _(u"(Serie-Número)"), cell_sub_table)
            sheet.write(1, 3, _(u"Número-Final"), cell_sub_table)

            sheet.merge_range(
                "E1:E2",
                _(u"Número Recepción"),
                cell_table,
            )
            sheet.merge_range(
                "F1:F2",
                _(u"Número Recepción Final"),
                cell_table,
            )
            sheet.merge_range(
                "G1:I1",
                _(u"NIF Expedidor"),
                cell_table,
            )
            sheet.write(1, 6, _(u"Tipo"), cell_sub_table)
            sheet.write(1, 7, _(u"Código País"), cell_sub_table)
            sheet.write(1, 8, _(u"Identificación"), cell_sub_table)
            sheet.merge_range(
                "J1:J2",
                _(u"Nombre Expedidor"),
                cell_table,
            )
            sheet.merge_range(
                "K1:K2",
                _(u"Factura Sustitutiva"),
                cell_table,
            )
            sheet.merge_range(
                "L1:L2",
                _(u"Clave de Operación"),
                cell_table,
            )
            sheet.merge_range(
                "M1:M2",
                _(u"Total Factura"),
                cell_table,
            )
            sheet.merge_range(
                "N1:N2",
                _(u"Base Imponible"),
                cell_table,
            )
            sheet.merge_range(
                "O1:O2",
                _(u"Tipo de IVA"),
                cell_table,
            )
            sheet.merge_range(
                "P1:P2",
                _(u"Cuota IVA Soportado"),
                cell_table,
            )
            sheet.merge_range(
                "Q1:Q2",
                _(u"Cuota Deducible"),
                cell_table,
            )
            sheet.merge_range(
                "R1:R2",
                _(u"Tipo de Recargo Eq."),
                cell_table,
            )
            sheet.merge_range(
                "S1:S2",
                _(u"Cuota Recargo Eq."),
                cell_table,
            )
            sheet.merge_range(
                "T1:W1",
                _(u"Pago"),
                cell_table,
            )
            sheet.write(1, 19, _(u"Fecha"), cell_sub_table)
            sheet.write(1, 20, _(u"Importe"), cell_sub_table)
            sheet.write(1, 21, _(u"Medio Utilizado"), cell_sub_table)
            sheet.write(
                1, 22, _(u"Identificación Medio Utilizado"), cell_sub_table
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
            row = 2
            taxes = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_RE"
            ).tax_ids.ids
            taxes2 = self.env.ref(
                "l10n_es_vat_book.aeat_vat_book_map_line_SFRETENCIONES"
            ).tax_ids.ids
            obj_tax = self.env["account.fiscal.position.tax"]
            for lin in lines:
                fiscal_pos = lin.invoice_id.fiscal_position_id or \
                    lin.partner_id.property_account_position_id
                if fiscal_pos:
                    for line in list(
                            set(lin.mapped("tax_line_ids.tax_id.amount"))):
                        tline = lin.tax_line_ids.filtered(
                            lambda r: r.tax_id.amount == line)[0]
                        lines_all = lin.tax_line_ids.filtered(
                            lambda r: r.tax_id.amount == line)
                        line = tline
                        tax_dest_id = False
                        if line.tax_id.id in taxes + taxes2:
                            continue
                        elif (line.tax_id.id in fiscal_pos.
                                tax_ids.mapped("tax_src_id").ids):
                            tax_dest_id = obj_tax.search([
                                ("position_id", "=", fiscal_pos.id),
                                ("tax_src_id", "=", line.tax_id.id),
                                ("tax_dest_id", "in", taxes)
                            ]).tax_dest_id
                            tax_dest_id = lin.tax_line_ids.filtered(
                                lambda r: r.tax_id == tax_dest_id
                            )
                        col = 0
                        partner = lin.partner_id
                        country_code = (
                            partner.country_id.code or (partner.vat or "")[:2]
                        ).upper()
                        # Fecha Expedición
                        date_invoice = (
                            lin.invoice_id.date_invoice or lin.move_id.date)
                        date_invoice = fields.Date.from_string(
                            date_invoice).strftime("%d/%m/%Y")
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
                                    lin.invoice_id.move_id.date
                                ).strftime("%d/%m/%Y"),
                                cell_table_center,
                            )
                        col += 1
                        # Serie-Numero
                        sheet.write(
                            row,
                            col,
                            lin.invoice_id.reference or (
                                lin.move_id.ref or ""
                            )[:20],
                            cell_table_right,
                        )
                        col += 1
                        # Número-Final
                        col += 1
                        # Número Recepción
                        sheet.write(
                            row, col, lin.entry_number, cell_table_right,
                        )
                        col += 1
                        # Número Recepción Final
                        col += 1
                        # Tipo
                        identifier = lin.invoice_id or lin.partner_id
                        tipo = _get_identifier(identifier, country_code)[:2]
                        sheet.write(row, col, tipo, cell_table_center)
                        col += 1
                        # Código País
                        sheet.write(
                            row, col, country_code, cell_table_left,
                        )
                        col += 1
                        # Identificación
                        if country_code != "ES":
                            vat = partner.vat or ""
                            vat = vat[:20]
                        else:
                            vat = (partner.vat and partner.vat[2:]) or ""
                        sheet.write(row, col, vat, cell_table_left)
                        col += 1
                        # Nombre expendidor
                        supplier = partner.name[:40]
                        sheet.write(row, col, supplier, cell_table_left)
                        col += 1
                        # Factura Sustitutiva
                        col += 1
                        # Clave de Operación
                        col += 1
                        # Total factura
                        base_imponible = sum(x.base_amount for x in lines_all)
                        cuota_iva_sop = sum(x.tax_amount for x in lines_all)
                        # Cuota de recargo eq.
                        cuota_req = 0
                        if tax_dest_id:
                            cuota_req = tax_dest_id.tax_amount
                        # Cuota de recargo eq.
                        total_factura = \
                            base_imponible + cuota_iva_sop + cuota_req
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(total_factura).replace(
                                ".", ",")[:13], cell_table_right
                        )
                        col += 1
                        # Base imponible
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(base_imponible).replace(
                                ".", ",")[:13],
                            cell_table_right,
                        )
                        col += 1
                        # Tipo de IVA
                        if line.tax_id.amount_type not in (
                                'fixed', 'percent', 'division'):
                            sheet.write(
                                row, col, 0, cell_table_right
                            )
                        else:
                            sheet.write(
                                row, col,
                                "{0:.2f}".format(line.tax_id.amount).replace(
                                    ".", ",")[:5], cell_table_right
                            )
                        col += 1
                        # Cuota IVA soportado
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(cuota_iva_sop).replace(
                                ".", ",")[:13], cell_table_right
                        )
                        col += 1
                        # Cuota Deducible
                        cuota_ded = self.env["l10n.es.vat.book.map"].search([(
                            "tax_ids.description",
                            "=",
                            line.tax_id.description),
                        ]).tax_id
                        cuota2 = self.env["account.tax"].search([
                            "|",
                            ("name", "=", cuota_ded.name),
                            ("description", "=", cuota_ded.description),
                            ("company_id", "=", self.env.user.company_id.id)
                        ])
                        if cuota2:
                            cuota_ded = lines_all.filtered(
                                lambda r: r.tax_id == cuota2)
                            cuota_ded = sum(
                                x.tax_amount for x in lines_all
                            ) - cuota_ded.tax_amount
                        else:
                            cuota_ded = 0
                        sheet.write(
                            row, col,
                            "{0:.2f}".format(cuota_ded).replace(".", ",")[
                                :13], cell_table_right
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
                                "{0:.2f}".format(
                                    tax_dest_id.tax_amount).replace(
                                    ".", ",")[:13], cell_table_right
                            )
                        col += 1
                        row += 1

        if book._context.get("issued"):
            lines = book.issued_line_ids + book.rectification_issued_line_ids
            fill_table_issued(lines, book)
        else:
            lines = book.received_line_ids + \
                book.rectification_received_line_ids
            fill_table_received(lines, book)


if ReportXlsx != object:
    VatNumberXlsx(
        'report.l10n_es_vat_book.l10n_es_vat_book_xlsx',
        'l10n.es.vat.book', parser=report_sxw.rml_parse,
    )
