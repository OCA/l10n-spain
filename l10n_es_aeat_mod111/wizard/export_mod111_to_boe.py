# -*- encoding: utf-8 -*-
##############################################################################
#                                                                            #
#  OpenERP, Open Source Management Solution.                                 #
#                                                                            #
#  @author Carlos Sánchez Cifuentes <csanchez@grupovermon.com>               #
#                                                                            #
#  This program is free software: you can redistribute it and/or modify      #
#  it under the terms of the GNU Affero General Public License as            #
#  published by the Free Software Foundation, either version 3 of the        #
#  License, or (at your option) any later version.                           #
#                                                                            #
#  This program is distributed in the hope that it will be useful,           #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of            #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              #
#  GNU Affero General Public License for more details.                       #
#                                                                            #
#  You should have received a copy of the GNU Affero General Public License  #
#  along with this program. If not, see <http://www.gnu.org/licenses/>.      #
#                                                                            #
##############################################################################

from openerp.osv import orm


class L10nEsAeatMod111ExportToBoe(orm.TransientModel):

    _inherit = 'l10n.es.aeat.report.export_to_boe'

    _name = 'l10n.es.aeat.mod111.export_to_boe'

    def _get_formatted_declaration_record(self, cr, uid, report, context=None):
        res = ''
        # Inicio del identificador de modelo y página (2)
        res += self._formatString('<T', 2)
        # Modelo (3)
        res += self._formatString('111', 3)
        # Página (2)
        res += self._formatString('01', 2)
        # Fin de identificador de modelo (1)
        res += self._formatString('>', 1)
        # Indicador de página complementaria (1)
        res += self._formatString('', 1)
        # Tipo de declaración (1)
        res += self._formatString(report.tipo_declaracion, 1)
        # NIF (9)
        res += self._formatString(report.company_vat, 9)
        # Denominación o Apellidos y Nombre (45)
        res += self._formatString(
            report.apellidos_razon_social
            if report.apellidos_razon_social
            else report.company_id.name, 30)
        res += self._formatString(report.nombre if report.nombre else '', 15)
        # Ejercicio (4)
        res += self._formatNumber(report.fiscalyear_id.code, 4)
        # Período (2)
        res += self._formatString(report.periodo, 2)
        return res

    def _get_formatted_main_record(self, cr, uid, report, context=None):
        res = ''
        # Rendimientos del trabajo.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Rendimientos del trabajo.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos del trabajo.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos del trabajo.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Rendimientos del trabajo.
        # Rendimientos en especie.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos del trabajo.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Rendimientos de actividades económicas.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Rendimientos de actividades económicas.
        # Rendimientos en especie.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Rendimientos de actividades económicas.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos en especie.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Premios por la participación en juegos, concursos, rifas
        # o combinaciones aleatorias.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos dinerarios.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos dinerarios.
        # Importe de las percepciones (17).
        res += self._formatNumber(0, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos dinerarios.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos en especie.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos
        # Rendimientos en especie
        # Importe de las percepciones (17)
        res += self._formatNumber(0, 17)
        # Ganancias patrimoniales derivadas de los aprovechamientos
        # forestales de los vecinos en los montes públicos.
        # Rendimientos en especie.
        # Importe de las retenciones (17).
        res += self._formatNumber(0, 17)
        # Contraprestaciones por la cesión de derechos de imagen,
        # ingresos a cuenta previstos en el artículo 92.8 de
        # la Ley del Impuesto.
        # Contrapartidas dinerarias o en especie.
        # N.º perceptores (8).
        res += self._formatNumber(0, 8)
        # Contraprestaciones por la cesión de derechos de imagen,
        # ingresos a cuenta previstos en el artículo 92.8 de
        # la Ley del Impuesto.
        # Contrapartidas dinerarias o en especie.
        # Contraprestaciones satisfechas (17).
        res += self._formatNumber(0, 17)
        # Contraprestaciones por la cesión de derechos de imagen,
        # ingresos a cuenta previstos en el artículo 92.8 de
        # la Ley del Impuesto.
        # Contrapartidas dinerarias o en especie.
        # Importe de los ingresos a cuenta (17).
        res += self._formatNumber(0, 17)
        # Total liquidación.
        # Suma de las retenciones e ingresos a cuenta (17).
        res += self._formatNumber(0, 17)
        # Total liquidación.
        # Resultado a ingresar de la anterior o anteriores
        # autoliquidaciones por el mismo concepto, ejercicio
        # y período (17).
        res += self._formatNumber(0, 17)
        # Total liquidación.
        # Resultado a ingresar (17).
        res += self._formatNumber(0, 17)
        return res

    def _get_formatted_other_records(self, cr, uid, report, context=None):
        res = ''
        # código de cuenta.
        # Entidad (4).
        res += self._formatNumber(0, 4)
        # Código de cuenta.
        # Sucursal (4).
        res += self._formatNumber(0, 4)
        # Código de cuenta.
        # DC (2).
        res += self._formatNumber(0, 2)
        # Código de cuenta.
        # Número de cuenta (10).
        res += self._formatNumber(0, 10)
        # Declaración complementaria (1).
        res += self._formatBoolean(report.complementaria, yes='1', no='0')
        # Número de justificante de la declaración anterior (13).
        res += self._formatString(
            report.numero_justificante_anterior
            if report.complementaria
            else '', 13)
        # Reservado para la Administración (16).
        res += self._formatString('', 16)
        # Nombre y apellidos de la persona de contacto (100).
        res += self._formatString('', 100)
        # Teléfono fijo de contacto (9).
        res += self._formatString('', 9)
        # Teléfono móvil de contacto (9).
        res += self._formatString('', 9)
        # Dirección de correo electrónico (50).
        res += self._formatString('', 50)
        # Reservado para el sello electrónico de la AEAT (13).
        res += self._formatString('', 13)
        # Reservado para la Administración (1).
        res += self._formatString('', 1)
        # Administración presentando declaración de
        # Colegio Concertado (1).
        # En blanco o 'X'.
        res += self._formatString('', 1)
        # Reservado para la Administración (459).
        res += self._formatString('', 459)
        # Indicador de fin de registro (9).
        res += self._formatString('</T11101>', 9)
        return res
