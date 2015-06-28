# -*- encoding: utf-8 -*-
##############################################################################
#
#  OpenERP, Open Source Management Solution.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api, fields


class L10nEsAeatMod216ExportToBoe(models.TransientModel):

    _inherit = 'l10n.es.aeat.report.export_to_boe'
    _name = 'l10n.es.aeat.mod216.export_to_boe'

    @api.multi
    def _get_formatted_declaration_record(self, report):
        res = ''
        #  Inicio del identificador de modelo y página: Constante "<T"
        res += self._formatString('<T', 2)
        # Modelo: Constante "216"
        res += self._formatString('216', 3)
        # Discriminante: Constante "01"
        res += self._formatString('0', 1)
        # Devengado. Ejercicio
        res += self._formatString(
            fields.Date.from_string(report.fiscalyear_id.date_start).year, 4)
        # Devengado. Periodo: "01" ... "12" o "1T" … "4T"
        res += self._formatString(
            fields.Date.from_string(report.period_id.date_start).month, 2,
            fill='0', align='>')
        # Tipo y cierre
        res += self._formatString('0000>', 5)
        return res

    @api.multi
    def _get_formatted_main_record(self, report):
        res = ''
        # Constante '<AUX>'(5)
        res += self._formatString('<AUX>', 5)
        # Reservado para el AEAT (Dejar en blanco)(300)
        res += self._formatString('', 300)
        # Constante '</AUX>'(6)
        res += self._formatString('</AUX>', 6)
        # Contenido del fichero.
        res += self._get_formatted_sub_declaration_record(report)
        res += self._get_formatted_sub_main_record(report)
        res += self._get_formatted_sub_other_records(report)
        return res

    @api.multi
    def _get_formatted_other_records(self, report):
        res = ''
        # Indicador de fin de registro (18).
        res += self._formatString('</T', 3)
        res += self._formatString('216', 3)
        res += self._formatString('0', 1)
        res += self._formatString(
            fields.Date.from_string(report.fiscalyear_id.date_start).year, 4)
        res += self._formatString(
            fields.Date.from_string(report.period_id.date_start).month, 2,
            fill='0', align='>')
        res += self._formatString('0000>', 5)
        # Fin de registro Constante CRLF(Hexadecimal 0D0A, Decimal 1310)
        res += '\x0A\x0D'
        return res

    @api.multi
    def _get_formatted_sub_declaration_record(self, report):
        res = ''
        # Inicio del identificador de modelo y página: Constante "<T"
        res += self._formatString('<T', 2)
        # Modelo: Constante "216"
        res += self._formatString('216', 3)
        # Página: Constante "01"
        res += self._formatString('01000', 5)
        # Fin de identificador de modelo: Constante ">"
        res += self._formatString('>', 1)
        # Indicador de página complementaria: En blanco
        res += self._formatString('', 1)
        # Tipo de declaración: I (ingreso), U (domiciliación),
        #                      G (ingreso a anotar en CCT), N (negativa)
        res += self._formatString(report.tipo_declaracion, 1)
        #  Identificación. Sujeto pasivo. NIF
        res += self._formatString(report.company_vat, 9)
        # Identificación. Sujeto pasivo. Denominación (o Apellidos y Nombre)
        res += self._formatString(report.company_id.name, 60)
        # Identificación. Nombre (solo personas fisicas)
        res += self._formatString('', 20)
        # Devengado. Ejercicio
        res += self._formatString(
            fields.Date.from_string(report.fiscalyear_id.date_start).year, 4)
        # Devengado. Periodo: "01" ... "12" o "1T" … "4T"
        res += self._formatString(
            fields.Date.from_string(report.period_id.date_start).month, 2,
            fill='0', align='>')
        return res

    @api.multi
    def _get_formatted_sub_main_record(self, report):
        res = ''
        # Liquidación
        # Partida 1
        # Num. Rentas
        res += self._formatNumber(report.casilla_01, 17)
        # Liquidación
        # Partida 2
        # Base ret. ing. cuenta.
        res += self._formatNumber(report.casilla_02, 17)
        # Liquidación
        # Partida 3
        # Retenciones ingresos a cuenta
        res += self._formatNumber(report.casilla_03, 17)
        # Liquidación
        # Partida 4
        # Num. Rentas
        res += self._formatNumber(report.casilla_04, 17)
        # Liquidación
        # Partida 5
        # Base ret. ing.cuenta.
        res += self._formatNumber(report.casilla_05, 17)
        # Liquidación
        # Partida 6
        # Resultado ing. anteriores declaraciones
        res += self._formatNumber(report.casilla_06, 17)
        # Liquidación
        # Partida 7
        # Resultado ingresar
        res += self._formatNumber(report.casilla_07, 17)
        return res

    @api.multi
    def _get_formatted_sub_other_records(self, report):
        res = ''
        # Domicializacion IBAN
        res += self._formatNumber(0, 34)
        # Declaración complementaria (1).
        res += self._formatString('1' if report.type == 'X' else '0', 1)
        # Número de justificante de la declaración anterior (13).
        res += self._formatString(report.previous_number
                                  if report.type == 'C' else '', 13)
        # Reservado para la AEAT (100).
        res += self._formatString('', 100)
        # Reservado para el sello electrónico de la AEAT (13).
        res += self._formatString('', 13)
        # Indicador de fin de registro (12).
        res += self._formatString('</T21601000>', 12)
        return res
