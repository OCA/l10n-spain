# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (c) 2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.tools.translate import _
from openerp.osv import orm


class L10nEsAeatMod340ExportToBoe(orm.TransientModel):
    _inherit = "l10n.es.aeat.mod340.export_to_boe"

    def _get_formated_presenter_record(self, report):
        """Returns a type 0, declaration/presenter, formated record.
        Only for Comunidad Foral de Navarra

        Format of the record:
            Tipo registro 0 – Registro de presentador:
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del presentador
            18-57 	Apellidos y nombre o razón social del presentador
            58-59       Domicilio - Siglas de la vía pública
            60-79       Domicilio - Nombre de la vía pública
            80-84       Domicilio - Número de la casa o punto kilométrico
            85-86       Domicilio - Escalera
            87-88       Domicilio - Piso
            89-90       Domicilio - Puerta
            91-95       Domicilio - Código postal
            96-107      Domicilio - Municipio del presentador
            108-109     Domicilio - Código provincia
            110-114     Total de declarantes
            115-123     Total de declarados
            124         Tipo de soporte
            125-133     Télefono de contacto
            134-173     Apellidos y nombre de la persona de contacto
            174-487     Relleno a blanco
            488-500     Sello electrónico
        """
        text = ''
        # Tipo de Registro
        text += '0'
        # Modelo Declaración
        text += '340'
        # Ejercicio
        text += self._formatString(report.fiscalyear_id.code, 4)
         # NIF del presentador
        text += self._formatString(report.presenter_vat or '', 9)
        # Apellidos y nombre del presentador
        text += self._formatString(report.presenter_name or '', 40)
        # Siglas de la vía pública
        text += self._formatString(report.presenter_address_acronym or '', 2)
        # Nombre de la vía pública
        text += self._formatString(report.presenter_address_name or '', 20)
        # Número de la casa
        text += self._formatNumber(report.presenter_address_number or 0, 5)
        # Escalera
        text += self._formatString(report.presenter_address_stair or '', 2)
        # Piso
        text += self._formatString(report.presenter_address_floor or '', 2)
        # Puerta
        text += self._formatString(report.presenter_address_door or '', 2)
        # Código postal
        text += self._formatNumber(int(report.presenter_city_id.zip or 0), 5)
        # Municipio
        text += self._formatString(report.presenter_city_id.name or '', 12)
        # Código postal
        if report.presenter_city_id:
            text += self._formatNumber(int(
                report.presenter_city_id.state_id.code), 2)
        else:
            text += 2 * ' '
        # Numero total de declarantes, actualmente solo 1
        text += '00001'
        # Número total de registros
        text += self._formatNumber(report.number_records, 9)
        # Tipo de soporte
        text += self._formatString(report.support_type, 1)
        # Persona de contacto (Teléfono)
        text += self._formatString(report.presenter_phone_contact or '', 9)
        # Persona de contacto (Apellidos y nombre)
        text += self._formatString(report.presenter_name_contact or '', 40)
        # Blancos
        text += 314 * ' '
        # Firma digital opcional, no implementado
        text += 13 * ' '
        text += '\r\n'

        assert len(text) == 502, \
            _("The type 0 record must be 500 characters long")
        return text

    def _get_formatted_other_records(self, cr, uid, report, context=None):
        file_contents = ''
        file_contents += self._get_formated_presenter_record(report)
        for invoice_issued in report.issued:
            file_contents += self._get_formatted_invoice_issued(
                cr, uid, report, invoice_issued)
        for invoice_received in report.received:
            file_contents += self._get_formatted_invoice_received(
                cr, uid, report, invoice_received)
        return file_contents
