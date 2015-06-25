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


class L10nEsAeatMod115ExportToBoe(models.TransientModel):

    _inherit = 'l10n.es.aeat.report.export_to_boe'
    _name = 'l10n.es.aeat.mod115.export_to_boe'

    @api.multi
    def _get_formatted_declaration_record(self, report):
        res = ''
        #  Inicio del identificador de modelo y página: Constante "<T"
        res += self._formatString('<T', 2)
        # Modelo: Constante "115"
        res += self._formatString('115', 3)
        # Página: Constante "01"
        res += self._formatString('01', 2)
        # Fin de identificador de modelo: Constante ">"
        res += self._formatString('000>', 4)
        # Reservado página complementaria
        res += self._formatString('C' if report.type == 'C' else ' ', 1)
        # Tipo de declaración: I (ingreso), U (domiciliación),
        #                      G (ingreso a anotar en CCT), N (negativa)
        res += self._formatString(report.tipo_declaracion, 1)
        # Identificación. Sujeto pasivo. NIF
        res += self._formatString(report.company_vat, 9)
        # Identificación. Sujeto pasivo. Denominación (o Apellidos y Nombre)
        res += self._formatString(report.company_id.name, 60)
        # Reservado para la Administración
        res += self._formatString('', 20)
        # Num Identificación. Ejercicio
        res += self._formatString(
            fields.Date.from_string(report.fiscalyear_id.date_start).year, 4)
        # Identificación. Periodo: "01" ... "12" o "1T" … "4T"
        res += self._formatString(
            fields.Date.from_string(report.period_id.date_start).month, 2,
            fill='0', align='>')
        return res

    @api.multi
    def _get_formatted_main_record(self, report):
        res = ''
        # Retenciones e ingresos a cuenta
        # N.º perceptores (15).
        res += self._formatNumber(report.casilla_01, 15)
        # Retenciones e ingresos a cuenta
        # Base retenciones e ingresos a cuenta (17).
        res += self._formatNumber(report.casilla_02, 17)
        # Retenciones e ingresos a cuenta
        # Retenciones e ingresos a cuenta (17).
        res += self._formatNumber(report.casilla_03, 17)
        # Retenciones e ingresos a cuenta
        # Resultado anteriores declaraciones (17).
        res += self._formatNumber(report.casilla_04, 17)
        # Retenciones e ingresos a cuenta
        # Resultado a ingresar (17).
        res += self._formatNumber(report.casilla_05, 17)
        return res

    @api.multi
    def _get_formatted_other_records(self, report):
        res = ''
        # Declaración complementaria (1).
        res += self._formatString('X' if report.type == 'C' else ' ', 1)
        # Número de justificante de la declaración anterior (13).
        res += self._formatString(report.previous_number
                                  if report.type == 'C' else '', 13)
        # Domicialización IBAN (34).
        res += self._formatString('', 34)
        # Reservado AEAT (236).
        res += self._formatString('', 236)
        # Reservado para la administración. Sello electronico (13).
        res += self._formatString('', 13)
        # Indicador de fin de registro (12).
        res += self._formatString('</T11501000>', 12)
        return res
