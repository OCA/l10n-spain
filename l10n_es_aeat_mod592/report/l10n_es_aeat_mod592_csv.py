# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import csv

from odoo import fields, models



class Mod592CsvManufacturer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_csv_man"
    _description = "Mod592 CSV Manufacturer"
    _inherit = "report.report_csv.abstract"

    def generate_csv_report(self, writer, data, objects):
        writer.writeheader()
        for obj in objects.manufacturer_line_ids:
            writer.writerow({
                'numero_asiento': obj.numero_asiento,
                'fecha_hecho': obj.fecha_hecho,
                'concepto': obj.concepto,
                'clave_producto': obj.clave_producto,
                'descripcion_producto': obj.descripcion_producto,
                'regimen_fiscal_manufacturer': obj.regimen_fiscal_manufacturer,
                'justificante': obj.justificante,
                'proveedor_tipo_documento': obj.proveedor_tipo_documento,
                'proveedor_numero_documento': obj.proveedor_numero_documento,
                'proveedor_razon_social': obj.proveedor_razon_social,
                'kilogramos': obj.kilogramos,
                'kilogramos_no_reciclados': obj.kilogramos_no_reciclados,
                'observaciones_asiento': obj.observaciones_asiento or "",
            })

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"].append("numero_asiento")
        res["fieldnames"].append("fecha_hecho")
        res["fieldnames"].append("concepto")
        res["fieldnames"].append("clave_producto")
        res["fieldnames"].append("descripcion_producto")
        res["fieldnames"].append("regimen_fiscal_manufacturer")
        res["fieldnames"].append("justificante")
        res["fieldnames"].append("proveedor_tipo_documento")
        res["fieldnames"].append("proveedor_numero_documento")
        res["fieldnames"].append("proveedor_razon_social")
        res["fieldnames"].append("kilogramos")
        res["fieldnames"].append("kilogramos_no_reciclados")
        res["fieldnames"].append("observaciones_asiento")
        res['delimiter'] = ';'
        res['quoting'] = csv.QUOTE_ALL
        return res


class Mod592CsvAcquirer(models.AbstractModel):
    _name = "report.l10n_es_aeat_mod592.l10n_es_aeat_mod592_csv_acquirer"
    _description = "Mod592 CSV Acquirer"
    _inherit = "report.report_csv.abstract"

    def generate_csv_report(self, writer, data, objects):
        writer.writeheader()
        for obj in objects.acquirer_line_ids:
            writer.writerow({
                'numero_asiento': obj.numero_asiento,
                'fecha_hecho': obj.fecha_hecho,
                'concepto': obj.concepto,
                'clave_producto': obj.clave_producto,
                'regimen_fiscal_adquirer': obj.regimen_fiscal_adquirer,
                'justificante': obj.justificante,
                'proveedor_tipo_documento': obj.proveedor_tipo_documento,
                'proveedor_numero_documento': obj.proveedor_numero_documento,
                'proveedor_razon_social': obj.proveedor_razon_social,
                'kilogramos': obj.kilogramos,
                'kilogramos_no_reciclados': obj.kilogramos_no_reciclados,
                'observaciones_asiento': obj.observaciones_asiento or "",
            })

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"].append("numero_asiento")
        res["fieldnames"].append("fecha_hecho")
        res["fieldnames"].append("concepto")
        res["fieldnames"].append("clave_producto")
        res["fieldnames"].append("regimen_fiscal_adquirer")
        res["fieldnames"].append("justificante")
        res["fieldnames"].append("proveedor_tipo_documento")
        res["fieldnames"].append("proveedor_numero_documento")
        res["fieldnames"].append("proveedor_razon_social")
        res["fieldnames"].append("kilogramos")
        res["fieldnames"].append("kilogramos_no_reciclados")
        res["fieldnames"].append("observaciones_asiento")
        res['delimiter'] = ';'
        res['quoting'] = csv.QUOTE_ALL
        return res
