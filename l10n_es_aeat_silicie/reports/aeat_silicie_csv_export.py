# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import csv

from odoo import models


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
        moves.generate_silicie_fields()
        for move in moves:
            if move.send_silicie or move.not_declare:
                continue
            values = move._prepare_values()
            writer.writerow(self.localize_floats(values))

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
