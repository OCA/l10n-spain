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


class L10nEsAeatMod303ExportToBoe(orm.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = 'l10n.es.aeat.mod303.export_to_boe'

    def _get_formatted_declaration_record(self, cr, uid, report, context=None):
        res = ''
        # cabecera
        res += "<T30301> "
        # Tipo de declaración - "Para impresión, cualquier caracter
        # alfanumérico o 'N' si la autoliquidación se declara SIN ACTIVIDAD"
        res += self._formatString("N" if report.sin_actividad else " ", 1)
        # Identificación (1)
        res += self._formatString(report.company_vat, 9)  # NIF del declarante
        # Apellidos o razón social.
        res += self._formatString(report.company_id.name, 30)
        res += self._formatString("", 15)  # Nombre
        res += self._formatBoolean(report.devolucion_mensual, yes='1', no='2')
        # devengo (2)
        res += self._formatNumber(report.fiscalyear_id.code, 4)
        res += self._formatString(report.period, 2)
        assert len(res) == 71, _("The identification (1) and income (2) must "
                                 "be 72 characters long")
        return res

    def _get_formatted_main_record(self, cr, uid, report, context=None):
        lines = report._get_report_lines(context=context)
        res = ''
        # IVA devengado
        # -- Regimen General y Recargo de Equivalencia - code_pair [1~18]
        codes = [
            # Régimen general
            ('[01]', '[03]'),
            ('[04]', '[06]'),
            ('[07]', '[09]'),
            # Recargo de equivalencia
            ('[10]', '[12]'),
            ('[13]', '[15]'),
            ('[16]', '[18]'),
        ]
        for code_pair in codes:
            base_imponible = lines.get(code_pair[0], 0)
            cuota = lines.get(code_pair[1], 0)
            tipo = cuota / base_imponible * 100 if base_imponible else 0
            # base imponible X %  -- codes [1, 4, 7, 10, 13, 16]
            res += self._formatNumber(base_imponible, 15, 2)
            # tipo % codes - [2, 5, 8, 11, 14, 17]
            res += self._formatNumber(tipo, 3,  2)
            # cuota X % -- codes [3, 6, 9, 12, 15, 18]
            res += self._formatNumber(cuota, 15, 2)
        # -- Adquisiciones Intracomunitarias - codes [19,20]
        res += self._formatNumber(lines.get("[19]"), 15, 2)  # base imponible
        res += self._formatNumber(lines.get("[20]"), 15, 2)  # cuota
        # -- Total Cuota Devengada - code [21]
        res += self._formatNumber(report.total_devengado, 15, 2)  # cuota
        # IVA deducible
        # -- Por Cuotas soportadas ... - codes [22~25]
        # -- Por Cuotas satisfechas en ... - codes [26~29]
        # -- En adquisiciones intracomunitarias de bienes ... - codes [30~33]
        for i in range(22, 34):
            res += self._formatNumber(lines.get("[%s]" % i), 15, 2)
        # --
        # Compesaciones Regimen Especial AG y P
        res += self._formatNumber(lines.get("[34]"), 15, 2)
        # Regularización inversiones
        res += self._formatNumber(lines.get("[35]"), 15, 2)
        # Regularización inversiones por aplicación del porcentaje
        # def de prorrata
        res += self._formatNumber(lines.get("[36]"), 15, 2)
        # -- Total a deducir
        res += self._formatNumber(report.total_deducir, 15, 2)
        # Diferencia [21] - [37]
        res += self._formatNumber(report.diferencia, 15, 2)
        # Atribuible a la administracion ...
        # TODO: Navarra y País Vasco
        res += self._formatNumber(report.porcentaje_atribuible_estado, 3, 2)
        res += self._formatNumber(report.atribuible_estado, 15, 2)
        res += self._formatNumber(report.cuota_compensar, 15, 2)  # [41]
        # Entregas intracomunitarias
        res += self._formatNumber(lines.get("[42]"), 15, 2)
        # [42], Exportaciones y operaciones asimiladas
        res += self._formatNumber(lines.get("[43]"), 15, 2)
        # [43], Derecho a deucción [44]
        res += self._formatNumber(lines.get("[44]"), 15, 2)
        # Estado y Comunidades Forales
        res += self._formatNumber(report.regularizacion_anual, 15, 2)
        # [40] - [41] --v
        res += self._formatNumber(report.resultado_casilla_46, 15, 2)
        # A deducir - autoliquidación complementaria .... pedir campo
        res += self._formatNumber(report.previus_result
                                  if report.complementaria else 0, 15, 2)
        res += self._formatNumber(report.resultado_liquidacion, 15, 2)  # [48]
        # A compensar
        res += self._formatNumber(report.compensar, 15, 2)  # [49]
        # Marca SIN ACTIVIDAD
        res += self._formatBoolean(report.sin_actividad, yes='1', no='2')
        assert len(res) == 822 - 72, (_("The vat records must be 749 characters"
                                        " long and are %s") % len(res))
        return res

    def _get_formatted_other_records(self, cr, uid, report, context=None):
        res = ''
        # devolucion (6)
        res += self._formatNumber(report.devolver, 15, 2)  # devolucion [50]
        ccc = ""
        if report.cuenta_devolucion_id and report.devolver:
            ccc = report.cuenta_devolucion_id.acc_number
            ccc = ccc.replace("-", "").replace(" ", "")
            if not (len(ccc) == 20 and ccc.isdigit()):
                raise orm.except_orm(
                    _('Warning'),
                    _("CCC de devolución no válida \n%s") % ccc)
        res += self._formatString(ccc, 20)  # no hay devolución
        """
        # ingreso (7)
        859     1     Num     Ingreso (7) - Forma de pago
        860     17    N       Ingreso (7) - Importe [I]
        877     4     An      Ingreso (7) - Código cuenta cliente - Entidad
        881     4     An      Ingreso (7) - Código cuenta cliente - Oficina
        885     2     An      Ingreso (7) - Código cuenta cliente - DC
        887     10    An      Ingreso (7) - Código cuenta cliente - Número de
                                                                    cuenta
        """
        # NO SE USA ??? Forma de Pago - "0" No consta, "1" Efectivo,
        # "2" Adeudo en cuenta, "3" Domiciliación
        res += self._formatString("0", 1)
        res += self._formatNumber(report.ingresar, 15, 2)  # devolucion [50]
        ccc = ""
        if report.cuenta_ingreso_id and report.ingresar:
            ccc = report.cuenta_ingreso_id.acc_number
            ccc = ccc.replace("-", "").replace(" ", "")
            if not (len(ccc) == 20 and ccc.isdigit()):
                raise orm.except_orm(_('Warning'),
                                     _("CCC de ingreso no válido %s") % ccc)
        res += self._formatString(ccc, 20)  # no hay devolución
        # Complementaria (8) Indicador Autoliquidación complementaria
        res += self._formatBoolean(report.complementaria, yes='1', no='0')
        # Complementaria (8) - no justificante declaración anterior
        res += self._formatString(report.previous_number
                                  if report.complementaria else "", 13)
        # TODO -- hardcode por ahora
        # Autorización conjunta
        res += self._formatBoolean(False, yes='1', no=' ')
        res += self._formatString(' ', 1)  # 77 autodeclaracion del concurso
        res += ' '*398  # campo reservado
        # Localidad
        res += self._formatString(report.company_id.partner_id.city, 16)
        # TODO: Utilizar formato del servidor
        date = datetime.strptime(report.calculation_date, "%Y-%m-%d %H:%M:%S")
        res += self._formatString(date.strftime("%d"), 2)  # fecha: Dia
        res += self._formatString(_(date.strftime("%B")), 10)  # fecha: Mes
        res += self._formatString(date.strftime("%Y"), 4)  # fecha: Año
        res += self._formatString("</T30301>", 9)
        res += "\r\n".encode("ascii")
        return res

    def _do_global_checks(self, report, contents, context=None):
        assert len(contents) == 1353, (
            _("The 303 report must be 1353 characters long and are %s")
            % len(contents))
        return True
