# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import csv
from odoo import models, exceptions, _


class AeatSiliceCsv(models.AbstractModel):
    _name = 'report.report_csv.aeat_silice_csv'
    _inherit = 'report.report_csv.abstract'

    @staticmethod
    def localize_floats(row):
        res = {}
        for key, value in row.items():
            if isinstance(value, float):
                value = str(value).replace('.', ',')
            res[key] = value
        return res

    def generate_csv_report(self, writer, data, moves):
        writer.writeheader()
        for obj in moves:
            if obj.send_silicie or obj.not_declare:
                continue
            if not obj.fields_check:
                raise exceptions.ValidationError(_('Check move validation!'))
            writer.writerow(
                self.localize_floats(
                    {'Número Referencia Interno': obj.id, 'Número Asiento Previo': '',
                     'Fecha Movimiento': obj.date.strftime('%d/%m/%Y'),
                     'Fecha Registro Contable': obj.date.strftime('%d/%m/%Y'),
                     'Tipo Movimiento': obj.silicie_move_type_id.code,
                     'Información adicional Diferencia en Menos': obj.silicie_loss_id.code
                     if obj.silicie_loss_id else '', 'Régimen Fiscal': obj.silice_tax_position,
                     'Tipo de Operación': obj.silicie_processing_id.code if obj.silicie_processing_id else '',
                     'Número Operación': obj.silicie_operation_num if obj.silicie_operation_num else '',
                     'Descripción Unidad de Fabricación': '', 'Código Unidad de Fabricación': '',
                     'Tipo Justificante': obj.silicie_proof_type_id.code, 'Número Justificante': obj.reference,
                     'Tipo Documento Identificativo': '', 'Número Documento Identificativo': '', 'Razón Social': '',
                     'CAE/Número Seed': '', 'Repercusión Tipo Documento Identificativo': '',
                     'Repercusión Número Documento Identificativo': '', 'Repercusión Razón Social': '', 'Epígrafe': '',
                     'Código Epígrafe': obj.epigraph_silicie_id.code, 'Código NC': obj.nc_code,
                     'Clave': obj.product_key_silicie_id.code, 'Cantidad': obj.qty_conversion_silicie,
                     'Unidad de Medida': obj.uom_silicie_id.code, 'Descripción de Producto': obj.product_id.name,
                     'Referencia Producto': obj.product_id.default_code, 'Densidad': '',
                     'Grado Alcohólico': obj.alcoholic_grade, 'Cantidad de Alcohol Puro': obj.absolute_alcohol,
                     'Porcentaje de Extracto': '', 'Kg. - Extracto': '', 'Grado Plato Medio': '', 'Grado Acético': '',
                     'Tipo de Envase': obj.container_type_silicie_id.code,
                     'Capacidad de Envase': obj.factor_conversion_silicie, 'Número de Envases': int(
                         obj.quantity_done),
                     'Observaciones': obj.notes_silice or '', }))

    def csv_report_options(self):
        res = super().csv_report_options()
        res['fieldnames'].append('Número Referencia Interno')
        res['fieldnames'].append('Número Asiento Previo')
        res['fieldnames'].append('Fecha Movimiento')
        res['fieldnames'].append('Fecha Registro Contable')
        res['fieldnames'].append('Tipo Movimiento')
        res['fieldnames'].append('Información adicional Diferencia en Menos')
        res['fieldnames'].append('Régimen Fiscal')
        res['fieldnames'].append('Tipo de Operación')
        res['fieldnames'].append('Número Operación')
        res['fieldnames'].append('Descripción Unidad de Fabricación')
        res['fieldnames'].append('Código Unidad de Fabricación')
        res['fieldnames'].append('Tipo Justificante')
        res['fieldnames'].append('Número Justificante')
        res['fieldnames'].append('Tipo Documento Identificativo')
        res['fieldnames'].append('Número Documento Identificativo')
        res['fieldnames'].append('Razón Social')
        res['fieldnames'].append('CAE/Número Seed')
        res['fieldnames'].append('Repercusión Tipo Documento Identificativo')
        res['fieldnames'].append('Repercusión Número Documento Identificativo')
        res['fieldnames'].append('Repercusión Razón Social')
        res['fieldnames'].append('Epígrafe')
        res['fieldnames'].append('Código Epígrafe')
        res['fieldnames'].append('Código NC')
        res['fieldnames'].append('Clave')
        res['fieldnames'].append('Cantidad')
        res['fieldnames'].append('Unidad de Medida')
        res['fieldnames'].append('Descripción de Producto')
        res['fieldnames'].append('Referencia Producto')
        res['fieldnames'].append('Densidad')
        res['fieldnames'].append('Grado Alcohólico')
        res['fieldnames'].append('Cantidad de Alcohol Puro')
        res['fieldnames'].append('Porcentaje de Extracto')
        res['fieldnames'].append('Kg. - Extracto')
        res['fieldnames'].append('Grado Plato Medio')
        res['fieldnames'].append('Grado Acético')
        res['fieldnames'].append('Tipo de Envase')
        res['fieldnames'].append('Capacidad de Envase')
        res['fieldnames'].append('Número de Envases')
        res['fieldnames'].append('Observaciones')

        res['delimiter'] = ';'
        res['quoting'] = csv.QUOTE_MINIMAL
        return res
