# -*- coding: utf-8 -*-
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


class L10nEsAeatMod111ExportToBoe(models.TransientModel):

    _inherit = 'l10n.es.aeat.report.export_to_boe'
    _name = 'l10n.es.aeat.mod111.export_to_boe'

    @api.multi
    def _get_formatted_declaration_record(self, report):
        res = ''
        #  Inicio del identificador de modelo y página: Constante "<T"
        res += self._formatString('<T', 2)
        # Modelo: Constante "111"
        res += self._formatString('111', 3)
        # Página: Constante "01"
        res += self._formatString('01', 2)
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
        res += self._formatString(report.company_id.name, 45)
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
        # Rendimientos del trabajo.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_01, 8)
        # Rendimientos del trabajo.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_02, 17)
        # Rendimientos del trabajo.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_03, 17)
        # Rendimientos del trabajo.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_04, 8)
        # Rendimientos del trabajo.
        # Rendimientos en especie.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_05, 17)
        # Rendimientos del trabajo.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_06, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_07, 8)
        # Rendimientos de actividades económicas.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_08, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_09, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_10, 8)
        # Rendimientos de actividades económicas.
        # Rendimientos en especie.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_11, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_12, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_13, 8)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_14, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_15, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_16, 8)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos en especie.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_17, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_18, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_19, 8)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(report.casilla_20, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_21, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_22, 8)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos
        # Rendimientos en especie
        # Importe de las percepciones (17)
        res += self._formatNumber(report.casilla_23, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(report.casilla_24, 17)
        # Contraprestaciones por la cesión de derechos de imagen,
        # ingresos a cuenta previstos en el artículo 92.8 de
        # la Ley del Impuesto.
        # Contrapartidas dinerarias o en especie.
        # N.º perceptores (8).
        res += self._formatNumber(report.casilla_25, 8)
        # Contraprestaciones por la cesión de derechos de imagen,
        # ingresos a cuenta previstos en el artículo 92.8 de
        # la Ley del Impuesto.
        # Contrapartidas dinerarias o en especie.
        # Contraprestaciones satisfechas (17).
        res += self._formatNumber(report.casilla_26, 17)
        # Contraprestaciones por la cesión de derechos de imagen,
        # ingresos a cuenta previstos en el artículo 92.8 de
        # la Ley del Impuesto.
        # Contrapartidas dinerarias o en especie.
        # Importe de los ingresos a cuenta (17).
        res += self._formatNumber(report.casilla_27, 17)
        # Total liquidación.
        # Suma de las retenciones e ingresos a cuenta (17).
        res += self._formatNumber(report.casilla_28, 17)
        # Total liquidación.
        # Resultado a ingresar de la anterior o anteriores
        # autoliquidaciones por el mismo concepto, ejercicio
        # y período (17).
        res += self._formatNumber(report.casilla_29, 17)
        # Total liquidación.
        # Resultado a ingresar (17).
        res += self._formatNumber(report.casilla_30, 17)
        return res

    @api.multi
    def _get_formatted_other_records(self, report):
        res = ''
        # Código de cuenta. Entidad (4).
        res += self._formatNumber(0, 4)
        # Código de cuenta. Sucursal (4).
        res += self._formatNumber(0, 4)
        # Código de cuenta. DC (2).
        res += self._formatNumber(0, 2)
        # Código de cuenta. Número de cuenta (10).
        res += self._formatNumber(0, 10)
        # Declaración complementaria (1).
        res += self._formatString('1' if report.type == 'C' else '0', 1)
        # Número de justificante de la declaración anterior (13).
        res += self._formatString(report.previous_number
                                  if report.type == 'C' else '', 13)
        # Reservado para la Administración (16).
        res += self._formatString('', 16)
        # Nombre y apellidos de la persona de contacto (100).
        res += self._formatString(report.contact_name, 100)
        # Teléfono fijo de contacto (9).
        res += self._formatString(report.contact_phone, 9)
        # Teléfono móvil de contacto (9).
        res += self._formatString(report.contact_mobile_phone, 9)
        # Dirección de correo electrónico (50).
        res += self._formatString('', 50)
        # Reservado para el sello electrónico de la AEAT (13).
        res += self._formatString('', 13)
        # Reservado para la Administración (1).
        res += self._formatString('', 1)
        # Administración presentando declaración de
        # Colegio Concertado (1).
        # En blanco o 'X'.
        res += self._formatBoolean(report.colegio_concertado)
        # Reservado para la Administración (459).
        res += self._formatString('', 459)
        # Indicador de fin de registro (9).
        res += self._formatString('</T11101>', 9)
        return res
