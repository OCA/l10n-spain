# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
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

__author__ = "Luis Manuel Angueira Blanco (Pexego)"


from osv import osv
from tools.translate import _


class l10n_es_aeat_mod347_export_to_boe(osv.osv_memory):

    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod347.export_to_boe"
    _description = "Export AEAT Model 347 to BOE format"

    def _get_formated_declaration_record(self, report):
        """
        Returns a type 1, declaration/company, formated record.

        Format of the record:
            Tipo registro 1 – Registro de declarante:
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del declarante
            18-57 	Apellidos y nombre o razón social del declarante
            58          Tipo de soporte
            59-67 	Teléfono contacto
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

        text += '1'                                           # Tipo de Registro
        text += '347'                                         # Modelo Declaración
        text += self._formatString(report.fiscalyear_id.code, 4)   # Ejercicio
        text += self._formatString(report.company_vat, 9)          # NIF del declarante
        text += self._formatString(report.company_id.name, 40)     # Apellidos y nombre o razón social del declarante
        text += self._formatString(report.support_type, 1)         # Tipo de soporte
        text += self._formatString(report.contact_phone, 9)       # Persona de contacto (Teléfono)
        text += self._formatString(report.contact_name, 40)        # Persona de contacto (Apellidos y nombre)
        text += self._formatNumber(report.number, 13)              # Número identificativo de la declaración
        text += self._formatString(report.type, 2).replace('N', ' ')                # Declaración complementaria o substitutiva
        text += self._formatNumber(report.previous_number, 13)     # Número identificativo de la declaración anterior
        text += self._formatNumber(report.total_partner_records, 9)          # Número total de personas y entidades
        text += self._formatNumber(report.total_amount, 13, 2)               # Importe total de las operaciones
        text += self._formatNumber(report.total_real_state_records, 9)       # Número total de inmuebles
        text += self._formatNumber(report.total_real_state_amount, 13, 2)    # Importe total de las operaciones de arrendamiento
        text += 207*' '                                       # Blancos
        text += self._formatString(report.representative_vat, 9)   # NIF del representante legal
        text += 88*' '                                        # Blancos
        text += 13*' '                                        # Sello electrónico
        text += '\r\n'

        assert len(text) == 502, _("The type 1 record must be 502 characters long")
        return text


    def _get_formated_partner_record(self, report, partner_record):
        """
        Returns a type 2, partner, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de declarado
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del declarante
            18-26 	NIF del declarado
            27-35 	NIF del representante legal
            36-75 	Apellidos y nombre, razón social o denominación del declarado
            76          Tipo de hoja
            77-80 	Código provincia/país
            81          Blancos
            82          Clave de operación
            83-97 	Importe de las operaciones
            98          Operación de seguro
            99          Arrendamiento local negocio
            100-114 	Importe percibido en metálico
            115-129 	Importe percibido por transmisiones de inmuebles sujetas a IVA
            130-134     Año de devengo de las operaciones en efectivo
            134-500 	Blancos
            488-500 	Sello electrónico
        """
        text = ''

        text += '2'                                                     # Tipo de Registro
        text += '347'                                                   # Modelo Declaración
        text += self._formatString(report.fiscalyear_id.code, 4)             # Ejercicio
        text += self._formatString(report.company_vat, 9)                    # NIF del declarante
        text += self._formatString(partner_record.partner_vat, 9)            # NIF del declarado
        text += self._formatString(partner_record.representative_vat, 9)     # NIF del representante legal
        text += self._formatString(partner_record.partner_id.name, 40)       # Apellidos y nombre, razón social o denominación del declarado
        text += 'D'                                                     # Tipo de hoja: Constante ‘D’.
        text += self._formatNumber(partner_record.partner_state_code, 2)     # Código provincia
        text += 3*' '                                                     # Blancos
        text += self._formatString(partner_record.operation_key, 1)          # Clave de operación
        text += self._formatNumber(partner_record.amount, 13, 2)             # Importe de las operaciones
        text += self._formatBoolean(partner_record.insurance_operation)                      # Operación de seguro
        text += self._formatBoolean(partner_record.bussiness_real_state_rent)                # Arrendamiento local negocio
        text += self._formatNumber(partner_record.cash_amount, 13, 2)                        # Importe percibido en metálico
        text += self._formatNumber(partner_record.real_state_transmissions_amount, 13, 2)    # Importe percibido por transmisiones de inmuebles sujetas a IVA
        text += partner_record.origin_fiscalyear_id and self._formatString(partner_record.origin_fiscalyear_id.code, 4) or 4*'0' #Año de devengo de las operaciones en efectivo
        text += 367*' '                                                 # Blancos
        text += '\r\n'                                                  # Sello electrónico

        assert len(text) == 502, _("The type 2-D record (partner) must be 502 characters long")
        return text


    def _get_formated_real_state_record(self, report, partner_record):
        """
        Returns a type 2, real state, formated record

        Format of the record:
            Tipo de Registro 2 – Registro de inmueble
            Posiciones 	Descripción
            1           Tipo de Registro
            2-4 	Modelo Declaración
            5-8 	Ejercicio
            9-17 	NIF del declarante
            18-26 	NIF del arrendatario
            27-35 	NIF del representante legal
            36-75 	Apellidos y nombre, razón social o denominación del declarado
            76          Tipo de hoja
            77-99 	Blancos
            100-114 	Importe de la operación
            115 	Situación del inmueble
            116-140 	Referencia catastral
            141-333 	Dirección y datos del inmueble
                141–145 TIPO DE VÍA
                146–195 NOMBRE VÍA PUBLICA
                196–198 TIPO DE NUMERACIÓN
                199–203 NUMERO DE CASA
                204-206 CALIFICADOR DEL NUMERO
                207–209 BLOQUE
                210–212 PORTAL
                213–215 ESCALERA
                216–218 PLANTA O PISO
                219–221 PUERTA
                222–261 COMPLEMENTO.
                262–291 LOCALIDAD O POBLACIÓN.
                292–321 MUNICIPIO
                322–326 CODIGO DE MUNICIPIO
                327-328 CODIGO PROVINCIA
                329-333 CODIGO POSTAL
            334-500 	Blancos
        """
        text = ''

        text += '2'                                                     # Tipo de Registro
        text += '347'                                                   # Modelo Declaración
        text += self._formatString(report.fiscalyear_id.code, 4)             # Ejercicio
        text += self._formatString(report.company_vat, 9)                    # NIF del declarante
        text += self._formatString(partner_record.partner_vat, 9)            # NIF del declarado
        text += self._formatString(partner_record.representative_vat, 9)     # NIF del representante legal
        text += self._formatString(partner_record.partner_id.name, 40)       # Apellidos y nombre, razón social o denominación del declarado
        text += 'I'                                                     # Tipo de hoja: Constante ‘I’.
        text += 23*' '                                                   # Blancos
        text += self._formatNumber(partner_record.amount, 13, 2)  # Importe de las operaciones
        text += self._formatNumber(partner_record.situation, 1)   # Situación del inmueble
        text += self._formatString(partner_record.reference, 25)  # Referencia catastral
        text += self._formatString(partner_record.address_type, 5)        # TIPO DE VÍA
        text += self._formatString(partner_record.address, 50)            # NOMBRE VÍA PUBLICA
        text += self._formatString(partner_record.number_type, 3)         # TIPO DE NUMERACIÓN
        text += self._formatNumber(partner_record.number, 5)              # NUMERO DE CASA
        text += self._formatString(partner_record.number_calification, 3) # CALIFICADOR DEL NUMERO
        text += self._formatString(partner_record.block, 3)               # BLOQUE
        text += self._formatString(partner_record.portal, 3)              # PORTAL
        text += self._formatString(partner_record.stairway, 3)            # ESCALERA
        text += self._formatString(partner_record.floor, 3)               # PLANTA O PISO
        text += self._formatString(partner_record.door, 3)                # PUERTA
        text += self._formatString(partner_record.complement, 40)         # COMPLEMENTO
        text += self._formatString(partner_record.city, 30)               # LOCALIDAD O POBLACIÓN
        text += self._formatString(partner_record.township, 30)           # MUNICIPIO
        text += self._formatString(partner_record.township_code, 5)       # CODIGO DE MUNICIPIO
        text += self._formatString(partner_record.state_code, 2)          # CODIGO PROVINCIA
        text += self._formatString(partner_record.postal_code, 5)         # CODIGO POSTAL
        text += 167*' '                                                 # Blancos
        text += '\r\n'                                                  # Sello electrónico

        assert len(text) == 502, _("The type 2-I record (real state) must be 502 characters long")
        return text


    def _get_formated_other_records(self, report):
        file_contents = ''

        for real_state_record in report.real_state_record_ids:
            file_contents += self._get_formated_real_state_record(report, real_state_record)

        return file_contents
    

    def _export_boe_file(self, cr, uid, ids, object_to_export, model=None, context=None):
        return super(l10n_es_aeat_mod347_export_to_boe, self)._export_boe_file(cr, uid, ids, object_to_export, model='347')

l10n_es_aeat_mod347_export_to_boe()
