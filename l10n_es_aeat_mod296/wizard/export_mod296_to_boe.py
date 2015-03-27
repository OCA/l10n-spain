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

from datetime import datetime
from openerp import models, api


class L10nEsAeatMod296ExportToBoe(models.TransientModel):

    _inherit = 'l10n.es.aeat.report.export_to_boe'
    _name = 'l10n.es.aeat.mod296.export_to_boe'

    @api.multi
    def _get_formatted_main_record(self, report):
        res = ''
        # N. total de perceptores
        res += self._formatNumber(report.casilla_01, 9)
        # Base retenciones e ingresos a cuenta
        res += self._formatNumber(report.casilla_02, 14, include_sign=True)
        # Retenciones e ingresos a cuenta
        res += self._formatNumber(report.casilla_03, 15)
        # Retenciones e ingresos a cuenta ingresados
        res += self._formatNumber(report.casilla_04, 15)
        # Espacios
        res += self._formatString('', 201)
        # Nif representante legal
        res += self._formatString(report.representative_vat, 9)
        # Espacios
        res += self._formatString('', 88)
        # Sello electronico
        res += self._formatString('', 13)
        return res

    @api.multi
    def _get_formatted_other_records(self, report):
        res = ''
        for line in report.lines296:
            res += self._get_formatted_sub_declaration_record(line)
            res += self._get_formatted_sub_main_record(line)
        return res

    @api.multi
    def _get_formatted_sub_declaration_record(self, line):
        report = line.mod296_id
        res = ''
        #  Inicio del identificador de modelo y página: Constante "<T"
        res += self._formatString('2', 1)
        # Modelo: Constante "296"
        res += self._formatString('296', 3)
        # Ejercicio
        res += self._formatString(report.fiscalyear_id.code, 4)
        # Nif declarante
        res += self._formatString(report.company_vat, 9)
        # Nif perceptor
        res += self._formatString(line.partner_id.vat, 9)
        # Nif representante legal
        res += self._formatString(report.representative_vat, 9)
        # F/J
        res += self._formatString(line.fisica_juridica, 1)
        # Apellidos y nombre, razón social o denominación del perceptor
        res += self._formatString(line.partner_id.name, 40)
        # Blancos
        res += self._formatString('', 14)
        return res

    @api.multi
    def _get_formatted_sub_main_record(self, line):
        res = ''
        # Fecha de devengo
        if line.fecha_devengo:
            fecha_devengo = datetime.strptime(line.fecha_devengo, '%Y-%m-%d')
            res += self._formatString(fecha_devengo.strftime("%d%m%Y"), 8)
        else:
            res += self._formatString('', 8)
        # Naturaleza
        res += self._formatString(line.naturaleza or '', 1)
        # Clave
        res += self._formatString(line.clave or '', 2)
        # Subclave
        res += self._formatString(line.subclave or '', 2)
        # Base retenciones e ingresos a cuenta
        res += self._formatNumber(line.base_retenciones_ingresos, 12,
                                  include_sign=True)
        # Porcentaje retencion
        res += self._formatNumber(line.porcentaje_retencion, 4)
        # Retenciones e ingresos a cuenta
        res += self._formatNumber(line.retenciones_ingresos, 13)
        # Mediador
        res += self._formatBoolean(line.mediador, 1)
        # Codigo
        res += self._formatString(line.codigo or '', 1)
        # Codigo emisor
        res += self._formatString(line.codigo_emisor, 12)
        # Pago
        res += self._formatString(line.pago or '', 1)
        # Tipo codigo
        res += self._formatString(line.tipo_codigo or '', 1)
        # Codigo cuenta valores
        # entidad
        res += self._formatString('', 4)
        # Codigo cuenta valores
        # sucursal
        res += self._formatString('', 4)
        # Codigo cuenta valores
        # d.c.
        res += self._formatString('', 5)
        # Codigo cuenta valores
        # numero cuenta
        res += self._formatString('', 10)
        # Pendiente
        res += self._formatBoolean(line.pendiente, 1)
        # Ejercicio devengo
        res += self._formatString(line.ejercicio_devengo.code or '', 4)
        # Fecha de inicio del prestamo
        res += self._formatString('', 8)
        # Fecha de vencimiento del prestamo
        res += self._formatString('', 8)
        # remuneracion
        res += self._formatNumber('', 5)
        # Al prestamista
        res += self._formatNumber('', 7)
        # compensaciones
        res += self._formatNumber('', 12)
        # Garantias
        res += self._formatNumber('', 12)
        # Direccion del perceptor
        # domicilio/address
        res += self._formatString(line.domicilio, 50)
        # Direccion del perceptor
        # complemento del domicilio
        res += self._formatString(line.complemento_domicilio, 40)
        # Direccion del perceptor
        # poblacion/ciudad
        res += self._formatString(line.poblacion, 30)
        # Direccion del perceptor
        # Provincia/estado/región
        res += self._formatString(line.provincia.name or '', 30)
        # Direccion del perceptor
        # codigo postal
        res += self._formatString(line.zip, 10)
        # Direccion del perceptor
        # codigo pais
        res += self._formatString(line.pais.code or '', 2)
        # Blancos
        res += self._formatString('', 44)
        # NIF en el pais de residencia
        res += self._formatString(line.nif_pais_residencia, 20)
        # Fecha de nacimiento
        if line.fecha_nacimiento:
            fecha_nacimiento = datetime.strptime(line.fecha_nacimiento,
                                                 '%Y-%m-%d')
            res += self._formatString(fecha_nacimiento.strftime("%d%m%Y"), 8)
        else:
            res += self._formatString('', 8)
        # Lugar de nacimiento
        # Ciudad
        res += self._formatString(line.ciudad_nacimiento, 35)
        # Lugar de nacimiento
        # Codigo pais
        res += self._formatString(line.pais_nacimiento.code or '', 2)
        # Pais o territorio de residencia fiscal
        res += self._formatString(line.pais_residencia_fiscal.code or '', 2)
        # Blancos
        res += self._formatString('', 1)
        return res
