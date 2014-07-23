# -*- encoding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################
from datetime import datetime
from openerp.tools.translate import _
from openerp.osv import orm
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT


class L10nEsAeatMod130ExportToBoe(orm.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = 'l10n.es.aeat.mod130.export_to_boe'

    def _cleanString(self, string):
        return string.replace("-", "").replace(" ", "").replace("/", "")

    def _get_formatted_declaration_record(self, cr, uid, report, context=None):
        res = ''
        # cabecera
        res += "13001 "
        # Tipo de declaración
        # B (resultado a deducir)
        # G (cuenta corriente tributaria-ingreso)
        # I (ingreso)
        # N (negativa)
        # U (domiciliación del ingreso en CCC)
        res += self._formatString(report.tipo_declaracion, 1)
        # Código Administración - No se usan
        res += self._formatString("", 5)
        # Identificación (1)
        res += self._formatString(report.company_vat, 9)  # NIF del declarante
        res += self._formatString(report.company_id.name, 4)  # Comienzo primer apellido
        res += self._formatString(report.company_id.name, 30)  # Apellidos
        res += self._formatString("", 15)  # Nombre
        res += self._formatNumber(report.fiscalyear_id.code, 4)  # Ejercicio
        res += self._formatString(report.period, 2)
        return res

    def _get_formatted_main_record(self, cr, uid, report, context=None):
        res = ''
        # I. Activ. económicas estimac. Directa - Ingresos computables [01]
        res += self._formatNumber(report.casilla_01, 11, 2)
        # I. Activ. económicas estimac. Directa - Gastos fiscalmente deducibles [02]
        res += self._formatNumber(report.casilla_02, 11, 2)
        # I. Activ. económicas estimac. Directa - Rendimiento neto [03]
        res += self._formatNumber(report.casilla_03, 11, 2)
        # I. Activ. económicas estimac. Directa - 20% de la casilla 03 [04]
        res += self._formatNumber(report.casilla_04, 11, 2)
        # I. Activ. económicas estimac. Directa - A deducir - De los trimestres anteriores [05]
        res += self._formatNumber(report.casilla_05, 11, 2)
        # I. Activ. económicas estimac. Directa - A deducir - Retenciones e ingr. a cuenta [06]
        res += self._formatNumber(report.casilla_06, 11, 2)
        # I. Activ. económicas estimac. Directa - Pago fraccionado previo del trimestre [07]
        res += self._formatNumber(report.casilla_07, 11, 2)
        # II. Activ. agrícola. estimac. directa - Volumen de ingresos [08]
        res += self._formatNumber(report.casilla_08, 11, 2)
        # II. Activ. agrícola. estimac. directa - 2% de la casilla 08 [09]
        res += self._formatNumber(report.casilla_09, 11, 2)
        # II. Activ. agrícola. estimac. directa - A deducir- Retenciones e ingr. a cuenta [10]
        res += self._formatNumber(report.casilla_10, 11, 2)
        # II. Activ. agrícola estimac. directa - Pago fraccionado previo del trimestre [11]
        res += self._formatNumber(report.casilla_11, 11, 2)
        # III. Total liquidación - Suma de pagos fraccionados previos del trimestre [12]
        res += self._formatNumber(report.casilla_12, 11, 2)
        # III. Total liquidación -Minoración por aplicación de la deducción. Artículo 80 bis [13]
        res += self._formatNumber(report.casilla_13, 11, 2)
        # III. Total liquidación - Diferencia (12) - (13) [14]
        res += self._formatNumber(report.casilla_14, 11, 2)
        # III. Total liquidación - A deducir - Resultados negativos de trimestres anteriores [15]
        res += self._formatNumber(report.casilla_15, 11, 2)
        # III. Total liquidación - Pago de préstamos para la adquisición de vivienda habitual [16]
        res += self._formatNumber(report.casilla_16, 11, 2)
        # III. Total liquidación - Total (14) - (15) [17]
        res += self._formatNumber(report.casilla_17, 11, 2)
        # III. Total liquidación - A deducir - Resultado de las anteriores declaraciones [18]
        res += self._formatNumber(report.casilla_18, 11, 2)
        # III. Total liquidación - Resultado de la declaración [19]
        res += self._formatNumber(report.result, 11, 2)
        return res

    def _get_formatted_other_records(self, cr, uid, report, context=None):
        res = ''
        # Ingreso (4) Importe del ingreso
        res += self._formatNumber(report.result if report.result > 0 else 0,
                                  11, 2)
        # Ingreso (4) Forma de pago - "0" No consta, "1" Efectivo,
        # "2" Adeudo en cuenta, "3" Domiciliación
        res += self._formatString("0", 1)
        # Ingreso (4) CCC - Entidad - Sucursal - DC - Nº de cuenta - SIN USO
        res += self._formatString("",  20)
        # A deducir (5) Declaración con resultado a deducir en los siguientes
        # pagos fraccionados
        res += self._formatBoolean(report.result < 0 and report.period != '4T',
                                   yes='X', no=' ')
        # Complementaria (7) Cod. electrónico declaración anterior
        res += self._formatString(report.previous_electronic_code if
                                  report.complementary else "", 16)
        # Complementaria (7) Nº justificante declaración anterior
        res += self._formatString(report.previous_declaration if
                                  report.complementary else "", 13)
        # Persona de contacto
        res += self._formatString(report.company_id.name, 100)
        # Teléfono
        res += self._formatString(self._cleanString(report.company_id.phone), 9)
        # Observaciones
        res += self._formatString(report.comments, 350)
        # Localidad
        res += self._formatString(report.company_id.partner_id.city, 16)
        date = datetime.strptime(report.calculation_date,
                                 DEFAULT_SERVER_DATETIME_FORMAT)
        # fecha: Dia
        res += self._formatString(date.strftime("%d"), 2)
        # fecha: Mes
        res += self._formatString(_(date.strftime("%B")), 10)
        # fecha: Año
        res += self._formatString(date.strftime("%Y"), 4)
        res += "\r\n".encode("ascii")
        return res

    def _do_global_checks(self, report, contents, context=None):
        assert len(contents) == 880, (
            "The 130 report must be 880 characters long and are %s" % len(contents)
        )
        return True
