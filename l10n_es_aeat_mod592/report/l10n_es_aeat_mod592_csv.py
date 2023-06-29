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
                'Número de asiento': obj.entry_number,
                'Fecha Hecho Contabilizado': obj.date_done.strftime("%d/%m/%Y"),
                'Concepto': obj.concept,
                'Clave Producto"': obj.product_key,
                'Descripción Producto': obj.product_description,
                'Régimen Fiscal': obj.fiscal_manufacturer,
                'Justificante': obj.proof,
                'Prov./Dest.: Tipo Documento': obj.supplier_document_type,
                'Prov./Dest.: Nº Documento': obj.supplier_document_number,
                'Prov./Dest.: Razón Social': obj.supplier_social_reason,
                'Kilogramos': obj.kgs,
                'Kilogramos No Reciclados': obj.no_recycling_kgs,
                'Observaciones': obj.entry_note or "",
            })

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"].append("Número de asiento")
        res["fieldnames"].append("Fecha Hecho Contabilizado")
        res["fieldnames"].append("Concepto")
        res["fieldnames"].append("Clave Producto")
        res["fieldnames"].append("Descripción Producto")
        res["fieldnames"].append("Régimen Fiscal")
        res["fieldnames"].append("Justificante")
        res["fieldnames"].append("Kilogramos")
        res["fieldnames"].append("Kilogramos No Reciclados")
        res["fieldnames"].append("Prov./Dest.: Tipo Documento")
        res["fieldnames"].append("Prov./Dest.: Nº Documento")
        res["fieldnames"].append("Prov./Dest.: Razón Social")
        res["fieldnames"].append("Observaciones")
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
                'Número de asiento': obj.entry_number,
                'Fecha Hecho Contabilizado': obj.date_done.strftime("%d/%m/%Y"),
                'Concepto': obj.concept,
                'Clave Producto': obj.product_key,
                'Descripción Producto': obj.fiscal_acquirer,
                'Justificante': obj.proof,
                'Kilogramos': obj.kgs,
                'Kilogramos No Reciclados': obj.no_recycling_kgs,
                'Prov./Dest.: Tipo Documento': obj.supplier_document_type,
                'Prov./Dest.: Nº Documento': obj.supplier_document_number,
                'Prov./Dest.: Razón Social': obj.supplier_social_reason,
                'Observaciones': obj.entry_note or "",
            })

    def csv_report_options(self):
        res = super().csv_report_options()
        res["fieldnames"].append("Número de asiento")
        res["fieldnames"].append("Fecha Hecho Contabilizado")
        res["fieldnames"].append("Concepto")
        res["fieldnames"].append("Clave Producto")
        res["fieldnames"].append("Descripción Producto")
        res["fieldnames"].append("Justificante")
        res["fieldnames"].append("Kilogramos")
        res["fieldnames"].append("Kilogramos No Reciclados")
        res["fieldnames"].append("Prov./Dest.: Tipo Documento")
        res["fieldnames"].append("Prov./Dest.: Nº Documento")
        res["fieldnames"].append("Prov./Dest.: Razón Social")
        res["fieldnames"].append("Observaciones")
        res['delimiter'] = ';'
        res['quoting'] = csv.QUOTE_ALL
        return res
