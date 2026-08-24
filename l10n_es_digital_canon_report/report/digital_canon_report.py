# Copyright 2025 Juan Carlos Oñate - Tecnativa <juancarlos.onate@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class DigitalCanonReport(models.AbstractModel):
    _name = "report.l10n_es_digital_canon_report.digital_canon_report"
    _inherit = "report.report_xlsx.abstract"
    _description = "Digital Canon Report"

    def _get_ws_params(self, wb, data, records):
        template = {
            "operation_type": {
                "header": {"value": "Tipo de Operación"},
                "data": {"value": self._render("operation_type")},
                "width": 20,
            },
            "equipo_aparato_soporte": {
                "header": {"value": "Seleccionar un equipo/aparato/soporte"},
                "data": {
                    "value": self._render(
                        "dict(line.product_id._fields['l10n_es_digital_canon'].selection)"
                        ".get(line.product_id.l10n_es_digital_canon)"
                    )
                },
                "width": 30,
            },
            "marca_comercializada": {
                "header": {"value": "Marca Comercializada"},
                "data": {
                    "value": self._render(
                        "line.product_id.product_tmpl_id.product_brand_id.name"
                    )
                },
                "width": 25,
            },
            "unidades_vendidas": {
                "header": {"value": "Unidades vendidas en la operación"},
                "data": {"value": self._render("line.quantity")},
                "width": 20,
            },
            "operacion_exceptuada": {
                "header": {"value": "Operación Exceptuada"},
                "data": {"value": self._render("'Sí' if is_exempted else 'No'")},
                "width": 20,
            },
            "tipo_exceptuacion": {
                "header": {"value": "Tipo de Exceptuación"},
                "data": {"value": self._render("exemption_type")},
                "width": 25,
            },
            "pais_destino": {
                "header": {"value": "País de Destino"},
                "data": {
                    "value": self._render(
                        "sale_pickings.partner_id.country_id.name "
                        "if sale_pickings.partner_id.country_id != country_es "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "con_compensacion": {
                "header": {"value": "Con compensación"},
                "data": {
                    "value": self._render(
                        "'Sí' "
                        "if (purchase_picking.partner_id.country_id == country_es "
                        "    and purchase_picking.partner_id."
                        "digital_canon_exempt_type != 'no_desglosa') "
                        "else 'No'"
                    )
                },
                "width": 20,
            },
            "razon_social_proveedor": {
                "header": {"value": "Razón Social Proveedor"},
                "data": {
                    "value": self._render(
                        "purchase_picking.partner_id.name "
                        "if operation_type == 'Mayorista/Minorista' "
                        "else ''"
                    )
                },
                "width": 30,
            },
            "nif_proveedor": {
                "header": {"value": "NIF Proveedor"},
                "data": {
                    "value": self._render(
                        "purchase_picking.partner_id.vat "
                        "if operation_type == 'Mayorista/Minorista' "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "num_factura_compra": {
                "header": {"value": "Nº Factura de Compra"},
                "data": {
                    "value": self._render(
                        "vendor_bill.name "
                        "if (operation_type == 'Mayorista/Minorista' "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 25,
            },
            "importe_total_compra": {
                "header": {"value": "Importe Total Fra. Compra"},
                "data": {
                    "value": self._render(
                        "vendor_bill.amount_total "
                        "if (operation_type == 'Mayorista/Minorista' "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 25,
            },
            "fecha_factura_compra": {
                "header": {"value": "Fecha Fra. Compra"},
                "data": {
                    "value": self._render(
                        "vendor_bill.invoice_date "
                        "if (operation_type == 'Mayorista/Minorista' "
                        "   and is_exempted) "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "id_factura_compra": {
                "header": {"value": "ID Fra. Compra"},
                "data": {
                    "value": self._render(
                        "vendor_bill.name "
                        "if (operation_type == 'Mayorista/Minorista' "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "razon_social_beneficiario": {
                "header": {"value": "Razón Social Beneficiario"},
                "data": {
                    "value": self._render(
                        "line.move_id.partner_id.name "
                        "if (line.quantity >= 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 30,
            },
            "nif_beneficiario": {
                "header": {"value": "NIF Beneficiario"},
                "data": {
                    "value": self._render(
                        "line.move_id.partner_id.vat "
                        "if (line.quantity >= 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "num_factura_venta": {
                "header": {"value": "Número Fra. Venta"},
                "data": {
                    "value": self._render(
                        "line.move_id.name "
                        "if (line.quantity >= 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 25,
            },
            "fecha_factura_venta": {
                "header": {"value": "Fecha Fra. Venta"},
                "data": {
                    "value": self._render(
                        "line.move_id.invoice_date "
                        "if (line.quantity >= 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "importe_total_venta": {
                "header": {"value": "Importe Total Fra. Venta"},
                "data": {
                    "value": self._render(
                        "line.move_id.amount_total "
                        "if (line.quantity >= 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 25,
            },
            "id_factura_venta": {
                "header": {"value": "Id Fra. Venta"},
                "data": {
                    "value": self._render(
                        "line.move_id.name "
                        "if (line.quantity >= 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 20,
            },
            "nombre_receptor": {
                "header": {"value": "Nombre y Apellidos receptor/Razón Social"},
                "data": {
                    "value": self._render(
                        "line.move_id.partner_id.name "
                        "if (line.quantity < 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 35,
            },
            "email": {
                "header": {"value": "Email"},
                "data": {
                    "value": self._render(
                        "(line.move_id.partner_id.email or '') "
                        "if (line.quantity < 10 "
                        "    and is_exempted) "
                        "else ''"
                    )
                },
                "width": 30,
            },
            "direccion_entrega": {
                "header": {"value": "Dirección entrega"},
                "data": {
                    "value": self._render(
                        "(sale_order."
                        " partner_shipping_id.contact_address "
                        " or '') "
                        "if (line.quantity < 10 "
                        "    and is_exempted "
                        "    and sale_order."
                        "        partner_shipping_id) "
                        "else ''"
                    )
                },
                "width": 40,
            },
            "direccion_facturacion": {
                "header": {"value": "Dirección Facturación"},
                "data": {
                    "value": self._render(
                        "(sale_order."
                        " partner_invoice_id.contact_address "
                        " or '') "
                        "if (line.quantity < 10 "
                        "    and is_exempted "
                        "    and not sale_order."
                        "            partner_shipping_id) "
                        "else ''"
                    )
                },
                "width": 40,
            },
        }
        wanted_list = list(template.keys())
        ws_params = {
            "ws_name": "Report",
            "generate_ws_method": "_canon_report",
            "title": "Reporte Canon Digital SGAE",
            "wanted_list": wanted_list,
            "col_specs": template,
        }
        return [ws_params]

    def _is_operation_exempted(self, line, sale_pickings, country_es):
        partner = line.move_id.partner_id
        picking_country = sale_pickings.partner_id.country_id
        is_exempted = (picking_country and picking_country != country_es) or bool(
            partner.digital_canon_exempt_type
        )
        return is_exempted

    def _get_digital_canon_exemption_label(self, line, sale_pickings, country_es):
        partner = line.move_id.partner_id
        picking_country = sale_pickings.partner_id.country_id
        if picking_country and picking_country != country_es:
            return "Exportaciones"
        if partner.digital_canon_exempt_type == "administracion":
            return "Administraciones Públicas"
        if partner.digital_canon_exempt_type == "certificado":
            return "Personas jurídicas o físicas con certificado de exceptuación"
        if partner.digital_canon_exempt_type == "productores":
            return "Productores audiovisuales y/o productores fonográficos"
        return ""

    def _get_lots_from_invoice_line(self, line):
        """Return the lots associated with the account.move.line,
        limited to the invoiced quantity and avoiding lots from unrelated
        deliveries.
        """
        lots = self.env["stock.lot"]
        for sol in line.sale_line_ids:
            qty_needed = line.quantity
            for sml in sol.move_ids.move_line_ids.filtered(
                lambda m: m.picking_id.picking_type_code == "outgoing"
                and m.state == "done"
            ):
                if qty_needed <= 0:
                    break
                take = min(sml.quantity, qty_needed)
                if take > 0 and sml.lot_id:
                    lots |= sml.lot_id
                    qty_needed -= take
        return lots

    def _canon_report(self, workbook, ws, ws_params, data, records):
        ws.set_portrait()
        self._set_column_width(ws, ws_params)
        row_pos = 0
        row_pos = self._write_ws_title(ws, row_pos, ws_params)
        col_specs = ws_params["wanted_list"]
        format_compra = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#FFD966",
                "border": 1,
                "text_wrap": True,
            }
        )
        format_venta_mayor = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#9BC2E6",
                "border": 1,
                "text_wrap": True,
            }
        )
        format_venta_menor = workbook.add_format(
            {
                "bold": True,
                "align": "center",
                "valign": "vcenter",
                "bg_color": "#A9D08E",
                "border": 1,
                "text_wrap": True,
            }
        )
        compra_start_idx = col_specs.index("con_compensacion")
        compra_end_idx = col_specs.index("id_factura_compra")
        ws.merge_range(
            row_pos,
            compra_start_idx,
            row_pos,
            compra_end_idx,
            "Datos de la compra",
            format_compra,
        )
        venta_mayor_start_idx = col_specs.index("razon_social_beneficiario")
        venta_mayor_end_idx = col_specs.index("id_factura_venta")
        ws.merge_range(
            row_pos,
            venta_mayor_start_idx,
            row_pos,
            venta_mayor_end_idx,
            "Venta a Cliente Exceptuado > o igual a 10 Unidades",
            format_venta_mayor,
        )
        venta_menor_start_idx = col_specs.index("nombre_receptor")
        venta_menor_end_idx = col_specs.index("direccion_facturacion")
        ws.merge_range(
            row_pos,
            venta_menor_start_idx,
            row_pos,
            venta_menor_end_idx,
            "Venta a Cliente Exceptuado < a 10 Unidades",
            format_venta_menor,
        )
        row_pos += 1
        # Write column headers with their format per block
        for idx, col_name in enumerate(col_specs):
            col_def = ws_params["col_specs"][col_name]
            value = col_def["header"]["value"]
            if compra_start_idx <= idx <= compra_end_idx:
                fmt = format_compra
            elif venta_mayor_start_idx <= idx <= venta_mayor_end_idx:
                fmt = format_venta_mayor
            elif venta_menor_start_idx <= idx <= venta_menor_end_idx:
                fmt = format_venta_menor
            else:
                fmt = workbook.add_format(
                    {
                        "bold": True,
                        "align": "center",
                        "valign": "vcenter",
                        "bg_color": "#D9D9D9",
                        "border": 1,
                        "text_wrap": True,
                    }
                )
            ws.write(row_pos, idx, value, fmt)
        ws.set_row(row_pos, 60)
        row_pos += 1
        ws.freeze_panes(row_pos, 0)
        data_format = workbook.add_format(
            {
                "align": "left",
                "valign": "vcenter",
                "border": 1,
            }
        )
        date_start = fields.Date.from_string(data.get("date_start"))
        date_end = fields.Date.from_string(data.get("date_end"))
        move_lines = self.env["account.move.line"].search(
            [
                ("move_id.move_type", "=", "out_invoice"),
                ("product_id.l10n_es_digital_canon", "!=", False),
                ("move_id.invoice_date", ">=", date_start),
                ("move_id.invoice_date", "<=", date_end),
                ("move_id.state", "=", "posted"),
            ]
        )
        country_es = self.env.ref("base.es")
        for line in move_lines:
            lots = self._get_lots_from_invoice_line(line)
            purchase_pickings = self.env["stock.picking"].search(
                [
                    ("move_line_ids.lot_id", "in", lots.ids),
                    ("picking_type_code", "=", "incoming"),
                    ("purchase_id", "!=", False),
                ]
            )
            if not purchase_pickings:
                continue
            sale_pickings = line.sale_line_ids.order_id.picking_ids.filtered(
                lambda p: p.picking_type_code == "outgoing" and p.state != "cancel"
            )[:1]
            for purchase_picking in purchase_pickings:
                operation_type = "Fabricante/Importador"
                if (
                    purchase_picking.partner_id
                    and purchase_picking.partner_id.country_id == country_es
                ):
                    operation_type = "Mayorista/Minorista"
                vendor_bill = (
                    purchase_picking.purchase_id.invoice_ids.filtered(
                        lambda inv: inv.state == "posted"
                    )[:1]
                    or purchase_picking.purchase_id.invoice_ids[:1]
                )
                sale_order = line.sale_line_ids[:1].order_id
                row_pos = self._write_line(
                    ws,
                    row_pos,
                    ws_params,
                    col_specs_section="data",
                    render_space={
                        "line": line,
                        "country_es": country_es,
                        "purchase_picking": purchase_picking,
                        "sale_pickings": sale_pickings,
                        "sale_order": sale_order,
                        "operation_type": operation_type,
                        "vendor_bill": vendor_bill,
                        "is_exempted": self._is_operation_exempted(
                            line, sale_pickings, country_es
                        ),
                        "exemption_type": self._get_digital_canon_exemption_label(
                            line, sale_pickings, country_es
                        ),
                    },
                    default_format=data_format,
                )
