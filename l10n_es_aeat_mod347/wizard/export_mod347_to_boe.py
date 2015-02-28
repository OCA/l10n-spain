# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
from openerp.osv import orm
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT
from datetime import datetime


class L10nEsAeatMod347ExportToBoe(orm.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod347.export_to_boe"

    def _get_formatted_declaration_record(self, cr, uid, report,
                                          context=None):
        """
        Returns a type 1, declaration/company, formated record.

        Format of the record:
            Tipo registro 1 – Registro de declarante:

            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	    Modelo Declaración
            5-8 	    Ejercicio
            9-17 	    NIF del declarante
            18-57 	    Apellidos y nombre o razón social del declarante
            58          Tipo de soporte
            59-67 	    Teléfono contacto
            68-107      Apellidos y nombre contacto
            108-120 	Número identificativo de la declaración
            121-122 	Declaración complementaria o substitutiva
            123-135 	Número identificativo de la declaración anterior
            136-144 	Número total de personas y entidades
            145-159 	Importe total de las operaciones
            160-168 	Número total de inmuebles
            169-183 	Importe total de las operaciones de arrendamiento
            184-390 	Blancos
            391-399 	NIF del representante legal
            400-487 	Blancos
            488-500 	Sello electrónico
        """
        text = ''
        # Tipo de Registro
        text += '1'
        # Modelo Declaración
        text += '347'
        # Ejercicio
        text += self._formatString(
            datetime.strptime(report.fiscalyear_id.date_start,
                              DEFAULT_SERVER_DATE_FORMAT).year, 4)
        # NIF del declarante
        text += self._formatString(report.company_vat, 9)
        # Apellidos y nombre o razón social del declarante
        text += self._formatString(report.company_id.name, 40)
        # Tipo de soporte
        text += self._formatString(report.support_type, 1)
        # Persona de contacto (Teléfono)
        text += self._formatString(report.contact_phone or 0, 9)
        # Persona de contacto (Apellidos y nombre)
        text += self._formatString(report.contact_name, 40)
        # Número identificativo de la declaración
        text += self._formatNumber(report.number, 13)
        # Declaración complementaria o substitutiva
        text += self._formatString(report.type, 2).replace('N', ' ')
        # Número identificativo de la declaración anterior
        text += self._formatNumber(report.previous_number, 13)
        # Número total de personas y entidades
        text += self._formatNumber(report.total_partner_records, 9)
        # Importe total de las operaciones
        text += self._formatNumber(report.total_amount, 13, 2, True)
        # Número total de inmuebles
        text += self._formatNumber(report.total_real_state_records, 9)
        # Importe total de las operaciones de arrendamiento
        text += self._formatNumber(report.total_real_state_amount, 13, 2,
                                   True)
        # Blancos
        text += 205 * ' '
        # NIF del representante legal
        text += self._formatString(report.representative_vat, 9)
        # Blancos
        text += 88 * ' '
        # Sello electrónico
        text += 13 * ' '
        text += '\r\n'
        assert len(text) == 502, \
            _("The type 1 record must be 502 characters long")
        return text

    def _get_formated_partner_record(self, report, partner_record):
        """Returns a type 2, partner, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de declarado

            Posiciones 	Descripción
            1           Tipo de Registro
            2-4         Modelo Declaración
            5-8         Ejercicio
            9-17        NIF del declarante
            18-26       NIF del declarado
            27-35       NIF del representante legal
            36-75       Apellidos y nombre, razón social o denominación del
                        declarado
            76          Tipo de hoja
            77-80       Código provincia/país
            81          Blancos
            82          Clave de operación
            83-98 	    Importe de las operaciones
            98          Operación de seguro
            99          Arrendamiento local negocio
            100-114     Importe percibido en metálico
            115-129     Importe percibido por transmisiones de inmuebles
                        sujetas a IVA
            130-134     Año de devengo de las operaciones en efectivo
            136-151     Importe de las operaciones del primer trimestre
            152-167     Importe percibido por transmisiones de inmuebles
                        sujetas a IVA del primer trimestre
            168-183     Importe de las operaciones del segundo trimestre
            184-199     Importe percibido por transmisiones de inmuebles
                        sujetas a IVA del segundo trimestre
            200-215     Importe de las operaciones del tercer trimestre
            216-231     Importe percibido por transmisiones de inmuebles
                        sujetas a IVA del tercer trimestre
            232-247     Importe de las operaciones del cuarto trimestre
            248-263     Importe percibido por transmisiones de inmuebles
                        sujetas a IVA del cuarto trimestre
            264-280     NIF del operador comunitario
            281         'X' si aplica el régimen especial de criterio de caja
            282         'X' si son operaciones con inversión de sujeto pasivo
            283         'X' si son operaciones vinculadas al régimen de
                        depósito distinto del aduanero
            284-299     Importe de la operaciones anuales de criterio de caja
            300-500     Blancos
        """
        text = ''
        # Tipo de Registro
        text += '2'
        # Modelo Declaración
        text += '347'
        # Ejercicio
        text += self._formatString(report.fiscalyear_id.code, 4)
        # NIF del declarante
        text += self._formatString(report.company_vat, 9)
        # NIF del declarado
        text += self._formatString(partner_record.partner_vat, 9)
        # NIF del representante legal
        text += self._formatString(partner_record.representative_vat, 9)
        # Apellidos y nombre, razón social o denominación del declarado
        text += self._formatString(partner_record.partner_id.name, 40)
        # Tipo de hoja: Constante ‘D’.
        text += 'D'
        # Código provincia
        text += self._formatNumber(partner_record.partner_state_code, 2)
        # Blancos
        text += 3 * ' '
        # Clave de operación
        text += self._formatString(partner_record.operation_key, 1)
        # Importe de las operaciones
        text += self._formatNumber(partner_record.amount, 13, 2, True)
        # Operación de seguro
        text += self._formatBoolean(partner_record.insurance_operation)
        # Arrendamiento local negocio
        text += self._formatBoolean(partner_record.bussiness_real_state_rent)
        # Importe percibido en metálico
        text += self._formatNumber(partner_record.cash_amount, 13, 2)
        # Importe percibido por transmisiones de inmuebles sujetas a IVA
        text += self._formatNumber(
            partner_record.real_state_transmissions_amount, 13, 2, True)
        # Año de devengo de las operaciones en efectivo
        text += (partner_record.origin_fiscalyear_id and
                 self._formatString(partner_record.origin_fiscalyear_id.code,
                                    4) or 4 * '0')
        # Importe de las operaciones del primer trimestre
        text += self._formatNumber(partner_record.first_quarter, 13, 2, True)
        # Importe percibido por transmisiones de inmuebles sujates a Iva Primer
        # Trimestre
        text += self._formatNumber(
            partner_record.first_quarter_real_state_transmission_amount, 13,
            2, True)
        # Importe de las operaciones del segundo trimestre
        text += self._formatNumber(partner_record.second_quarter, 13, 2, True)
        # Importe percibido por transmisiones de inmuebles sujates a Iva
        # Segundo Trimestre
        text += self._formatNumber(
            partner_record.second_quarter_real_state_transmission_amount, 13,
            2, True)
        # Importe de las operaciones del tercer trimestre
        text += self._formatNumber(partner_record.third_quarter, 13, 2, True)
        # Importe percibido por transmisiones de inmuebles sujates a Iva Tercer
        # Trimestre
        text += self._formatNumber(
            partner_record.third_quarter_real_state_transmission_amount, 13,
            2, True)
        # Importe de las operaciones del cuarto trimestre
        text += self._formatNumber(partner_record.fourth_quarter, 13, 2, True)
        # Importe percibido por transmisiones de inmuebles sujates a Iva Cuarto
        # Trimestre
        text += self._formatNumber(
            partner_record.fourth_quarter_real_state_transmission_amount, 13,
            2, True)
        text += self._formatString(partner_record.community_vat, 17)
        text += self._formatBoolean(partner_record.cash_basis_operation)
        text += self._formatBoolean(partner_record.tax_person_operation)
        text += self._formatBoolean(partner_record.related_goods_operation)
        # Importe en criterio de caja
        text += self._formatNumber(0.0, 13, 2, True)
        # Blancos
        text += 201 * ' '
        # Sello electrónico
        text += '\r\n'
        assert len(text) == 502, \
            _("The type 2-D record (partner) must be 502 characters long")
        return text

    def _get_formated_real_state_record(self, report, partner_record):
        """
        Returns a type 2, real state, formated record
        Format of the record:
            Tipo de Registro 2 – Registro de inmueble

            Posiciones Descripción
            1          Tipo de Registro
            2-4        Modelo Declaración
            5-8        Ejercicio
            9-17       NIF del declarante
            18-26      NIF del arrendatario
            27-35      NIF del representante legal
            36-75      Apellidos y nombre, razón social o denominación del
                       declarado
            76         Tipo de hoja
            77-99      Blancos
            100-114    Importe de la operación
            115        Situación del inmueble
            116-140    Referencia catastral
            141-333    Dirección y datos del inmueble
            141–145    TIPO DE VÍA
            146–195    NOMBRE VÍA PUBLICA
            196–198    TIPO DE NUMERACIÓN
            199–203    NUMERO DE CASA
            204-206    CALIFICADOR DEL NUMERO
            207–209    BLOQUE
            210–212    PORTAL
            213–215    ESCALERA
            216–218    PLANTA O PISO
            219–221    PUERTA
            222–261    COMPLEMENTO.
            262–291    LOCALIDAD O POBLACIÓN.
            292–321    MUNICIPIO
            322–326    CODIGO DE MUNICIPIO
            327-328    CODIGO PROVINCIA
            329-333    CODIGO POSTAL
            334-500    Blancos
        """
        text = ''
        # Tipo de Registro
        text += '2'
        # Modelo Declaración
        text += '347'
        # Ejercicio
        text += self._formatString(report.fiscalyear_id.code, 4)
        # NIF del declarante
        text += self._formatString(report.company_vat, 9)
        # NIF del declarado
        text += self._formatString(partner_record.partner_vat, 9)
        # NIF del representante legal
        text += self._formatString(partner_record.representative_vat, 9)
        # Apellidos y nombre, razón social o denominación del declarado
        text += self._formatString(partner_record.partner_id.name, 40)
        # Tipo de hoja: Constante ‘I’.
        text += 'I'
        # Blancos
        text += 22 * ' '
        # Importe de las operaciones
        text += self._formatNumber(partner_record.amount, 13, 2, True)
        # Situación del inmueble
        text += self._formatNumber(partner_record.situation, 1)
        # Referencia catastral
        text += self._formatString(partner_record.reference, 25)
        # TIPO DE VÍA
        text += self._formatString(partner_record.address_type, 5)
        # NOMBRE VÍA PUBLICA
        text += self._formatString(partner_record.address, 50)
        # TIPO DE NUMERACION
        text += self._formatString(partner_record.number_type, 3)
        # NUMERO DE CASA
        text += self._formatNumber(partner_record.number, 5)
        # CALIFICADOR DEL NUMERO
        text += self._formatString(partner_record.number_calification, 3)
        # BLOQUE
        text += self._formatString(partner_record.block, 3)
        # PORTAL
        text += self._formatString(partner_record.portal, 3)
        # ESCALERA
        text += self._formatString(partner_record.stairway, 3)
        # PLANTA O PISO
        text += self._formatString(partner_record.floor, 3)
        # PUERTA
        text += self._formatString(partner_record.door, 3)
        # COMPLEMENTO
        text += self._formatString(partner_record.complement, 40)
        # LOCALIDAD O POBLACIÓN
        text += self._formatString(partner_record.city, 30)
        # MUNICIPIO
        text += self._formatString(partner_record.township, 30)
        # CODIGO DE MUNICIPIO
        text += self._formatString(partner_record.township_code, 5)
        # CODIGO PROVINCIA
        text += self._formatString(partner_record.state_code, 2)
        # CODIGO POSTAL
        text += self._formatString(partner_record.postal_code, 5)
        # Blancos
        text += 167 * ' '
        # Sello electrónico
        text += '\r\n'
        assert len(text) == 502, \
            _("The type 2-I record (real state) must be 502 characters long")
        return text

    def _get_formatted_main_record(self, cr, uid, report, context=None):
        res = ''
        for partner_record in report.partner_record_ids:
            res += self._get_formated_partner_record(report, partner_record)
        for real_state_record in report.real_state_record_ids:
            res += self._get_formated_real_state_record(report,
                                                        real_state_record)
        return res
