# Copyright 2019 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
import csv

from odoo import _, exceptions, models


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
        Lots = self.env['stock.production.lot']
        a14_type = self.env.ref(
            'l10n_es_aeat_silicie.aeat_move_type_silicie_a14')
        writer.writeheader()
        for move in moves:
            if move.send_silicie or move.not_declare:
                continue
            lot_moves = []
            for group in self.env['stock.move.line'].read_group([
                    ('move_id', 'in', move.ids)],
                    ['lot_id', 'qty_done'],
                    ['lot_id']):
                lot_moves.append({
                    'lot_id': group['lot_id'][0],
                    'qty_done': group['qty_done'],
                })
            for item in lot_moves:
                is_alcohol = move.product_id.silicie_product_type == 'alcohol'
                is_beer = move.product_id.silicie_product_type == "beer"
                absolute_alcohol = ''
                container_code = ''
                factor_conversion = ''
                qty_done = ''
                extract = ''
                kg_extact = ''
                density = ''
                grado_plato = ''
                partner_name = move.picking_id.partner_id.name or ''
                alcoholic_grade = move.alcoholic_grade
                if is_alcohol:
                    absolute_alcohol = move.absolute_alcohol
                    container_code = move.container_type_silicie_id.code
                    factor_conversion = move.factor_conversion_silicie
                    qty_done = int(move.quantity_done)
                if is_beer:
                    qty_done = item['qty_done']
                    if move.product_id.product_class == "raw":
                        lot = Lots.browse(item['lot_id'])
                        extract = lot.extract
                        if move.silicie_move_type_id == a14_type:
                            kg_extact = extract * qty_done
                        if move.product_id.product_class == "manufactured":
                            alcoholic_grade = ""
                            density = lot.density
                            grado_plato = (density * 1000 - 1000) / 4
                writer.writerow(
                    self.localize_floats({
                        'Número Referencia Interno': move.id,
                        'Número Asiento Previo': '',
                        'Fecha Movimiento': move.date.strftime('%d/%m/%Y'),
                        'Fecha Registro Contable': move.date.strftime('%d/%m/%Y'),
                        'Tipo Movimiento': move.silicie_move_type_id.code,
                        'Información adicional Diferencia en Menos':
                            move.silicie_loss_id.code if move.silicie_loss_id else '',
                        'Régimen Fiscal': move.silice_tax_position,
                        'Tipo de Operación':
                            move.silicie_processing_id.code if
                            move.silicie_processing_id else '',
                        'Número Operación':
                            move.silicie_operation_num if
                            move.silicie_operation_num else '',
                        'Descripción Unidad de Fabricación': '',
                        'Código Unidad de Fabricación': '',
                        'Tipo Justificante': move.silicie_proof_type_id.code,
                        'Número Justificante': move.reference,
                        'Tipo Documento Identificativo': '1',
                        'Número Documento Identificativo':
                            move.picking_id.partner_id.vat or
                            move.company_id.vat or '',
                        'Razón Social': partner_name[:125],
                        'CAE/Número Seed': '',
                        'Repercusión Tipo Documento Identificativo': '',
                        'Repercusión Número Documento Identificativo': '',
                        'Repercusión Razón Social': '',
                        'Epígrafe': move.epigraph_silicie_id.fiscal_epigraph_silicie or '',
                        'Código Epígrafe': move.epigraph_silicie_id.code or '',
                        'Código NC': move.nc_code,
                        'Clave': move.product_key_silicie_id.code or '',
                        'Cantidad': move.qty_conversion_silicie,
                        'Unidad de Medida': move.uom_silicie_id.code,
                        'Descripción de Producto': move.product_id.name.strip(),
                        'Referencia Producto': move.product_id.default_code,
                        'Densidad': density,
                        'Grado Alcohólico': alcoholic_grade,
                        'Cantidad de Alcohol Puro': absolute_alcohol,
                        'Porcentaje de Extracto': extract,
                        'Kg. - Extracto': kg_extact,
                        'Grado Plato Medio': grado_plato,
                        'Grado Acético': '',
                        'Tipo de Envase': container_code,
                        'Capacidad de Envase': factor_conversion,
                        'Número de Envases': qty_done,
                        'Observaciones': move.notes_silice or '',
                    }))

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
