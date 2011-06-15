# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Inform�ticos. All Rights Reserved
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

__author__ = "Luis Manuel Angueira Blanco (Pexego)"


from osv import osv
from tools.translate import _

class l10n_es_aeat_mod349_export_to_boe(osv.osv_memory):

    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod349.export_to_boe"
    _description = "Export AEAT Model 349 to BOE format"


    def _get_company_name_with_title(self, company_obj):
        """
        Returns company name with title
        """
        if company_obj.partner_id and \
            company_obj.partner_id.title:
                return company_obj.name + ' ' + company_obj.partner_id.title.capitalize()

        return company_obj.name


    def _get_formated_declaration_record(self, report):
        """
        Returns a type 1, declaration/company, formated record.

            · All amounts must be positives
            · Numeric fields with no data must be filled with zeros
            · Alfanumeric/Alfabetic fields with no data must be filled with empty spaces
            · Numeric fields must be right aligned and filled with zeros on the left
            · Alfanumeric/Alfabetic fields must be uppercase left aligned,
              filled with empty spaces on right side. No special characters allowed
              unless specified in field description

        Format of the record:
            Tipo registro 1 – Registro de declarante:
            Posiciones  Naturaleza      Descripción
            1           Numérico        Tipo de Registro            Constante = '1'
            2-4         Numérico        Modelo Declaración          Constante = '349'
            5-8         Numérico        Ejercicio
            9-17        Alfanumérico    NIF del declarante
            18-57       Alfanumérico    Apellidos y nombre o razón social del declarante
            58          Alfabético      Tipo de soporte
            59-67       Numérico (9)    Teléfono contacto
            68-107      Alfabético      Apellidos y nombre contacto
            108-120 	Numérico        Número identificativo de la declaración
            121-122 	Alfabético      Declaración complementaria o substitutiva
            123-135 	Numérico        Número identificativo de la declaración anterior
            136-137     Alfanumérico    Período
            138-146     Numérico        Número total de operadores intracomunitarios
            147-161     Numérico        Importe de las operaciones intracomunitarias
            - 147-159     Numérico        Importe de las operaciones intracomunitarias (parte entera)
            - 160-161     Numérico        Importe de las operaciones intracomunitarias (parte decimal)
            162-170     Numérico        Número total de operadores intracomunitarios con rectificaciones
            171-185     Numérico        Importe total de las rectificaciones
            - 171-183     Numérico        Importe total de las rectificaciones (parte entera)
            - 184-185     Numérico        Importe total de las rectificaciones (parte decimal)
            186         Alfabético      Indicador cambio periodicidad en la obligación a declarar (X o '')
            187-390     Blancos         ----------------------------------------
            391-399     Alfanumérico    NIF del representante legal
            400-487     Blancos         ----------------------------------------
            488-500 	Sello electrónico
        """

        assert report, 'No Report defined'

        try:
            fiscal_year = int((report.fiscalyear_id.code or '')[:4])
        except:
            raise osv.except_osv(_('Fiscal year code'), _('First four characters of fiscal year code must be numeric and contain the fiscal year number. Please, fix it and try again.'))

        company_name = self._get_company_name_with_title(report.company_id)
        period = report.period_selection == 'MO' and report.month_selection or report.period_selection

        text = ''                                                               ## Empty text

        text += '1'                                                             # Tipo de Registro
        text += '349'                                                           # Modelo Declaración
        text += self._formatNumber(fiscal_year, 4)                              # Ejercicio
        text += self._formatString(report.company_vat, 9)                       # NIF del declarante
        text += self._formatString(company_name, 40)                            # Apellidos y nombre o razón social del declarante
        text += self._formatString(report.support_type, 1)                      # Tipo de soporte
        text += self._formatString(report.contact_phone.replace(' ', ''), 9)    # Persona de contacto (Teléfono)
        text += self._formatString(report.contact_name, 40)                     # Persona de contacto (Apellidos y nombre)
        text += self._formatNumber(report.number, 13)                           # Número identificativo de la declaración
        text += self._formatString(report.type, 2).replace('N', ' ')            # Declaración complementaria o substitutiva
        text += self._formatNumber(report.previous_number, 13)                  # Número identificativo de la declaración anterior
        text += self._formatString(period, 2)                                   # Período
        text += self._formatNumber(report.total_partner_records, 9)             # Número total de operadores intracomunitarios
        text += self._formatNumber(report.total_partner_records_amount, 13, 2)  # Importe total de las operaciones intracomunitarias (parte entera)
        text += self._formatNumber(report.total_partner_refunds, 9)             # Número total de operadores intracomunitarios con rectificaciones
        text += self._formatNumber(report.total_partner_refunds_amount, 13, 2)  # Importe total de las rectificaciones
        text += self._formatBoolean(report.frequency_change)                    # Indicador cambio periodicidad en la obligación a declarar
        text += 204*' '                                                         # Blancos
        text += self._formatString(report.representative_vat, 9)                # NIF del representante legal
        text += 88*' '                                                          # Blancos
        text += 13*' '                                                          # Sello electrónico
        text += '\r\n'                                                          # Retorno de carro + Salto de línea

        assert len(text) == 502, _("The type 1 record must be 502 characters long")
        return text


    def _get_formated_partner_record(self, report, partner_record):
        """
        Returns a type 2, partner record

        Format of the record:
            Tipo registro 2
            Posiciones  Naturaleza      Descripción
            1           Numérico        Tipo de Registro            Constante = '2'
            2-4         Numérico        Modelo Declaración          Constante = '349'
            5-8         Numérico        Ejercicio
            9-17        Alfanumérico    NIF del declarante
            18-75       Blancos         ----------------------------------------
            76-92       Alfanumérico    NIF operador Intracomunitario
            - 76-77       Alfanumérico    Codigo de País
            - 78-92       Alfanumérico    NIF
            93-132      Alfanumérico    Apellidos y nombre o razón social del operador intracomunitario
            133         Alfanumérico    Clave de operación
            134-146     Numérico        Base imponible
            - 134-144     Numérico        Base imponible (parte entera)
            - 145-146     Numérico        Base imponible (parte decimal)
            147-500     Blancos         ----------------------------------------
        """

        assert report, 'No AEAT 349 Report defined'
        assert partner_record, 'No Partner record defined'

        text = ''

        try:
            fiscal_year = int((report.fiscalyear_id.code or '')[:4])
        except:
            raise osv.except_osv(_('Fiscal year code'), _('First four characters of fiscal year code must be numeric and contain the fiscal year number. Please, fix it and try again.'))

        ## Formateo de algunos campos (debido a que pueden no ser correctos)
        ## NIF : Se comprueba que no se incluya el código de pais
        company_vat = report.company_vat
        if len(report.company_vat) > 9:
            company_vat = report.company_vat[2:]

        text += '2'                                                                 # Tipo de registro
        text += '349'                                                               # Modelo de declaración
        text += self._formatNumber(fiscal_year, 4)                                  # Ejercicio
        text += self._formatString(company_vat, 9)                                  # NIF del declarante
        text += 58*' '                                                              # Blancos
        text += self._formatString(partner_record.partner_vat, 17)                  # NIF del operador intracomunitario
        text += self._formatString(partner_record.partner_id.name, 40)              # Apellidos y nombre o razón social del operador intracomunitario
        text += self._formatString(partner_record.operation_key, 1)                 # Clave de operación
        text += self._formatNumber(partner_record.total_operation_amount, 11, 2)    # Base imponible (parte entera)

        text += 354*' '                                                             # Blancos
        text +='\r\n'                                                               # Retorno de carro + Salto de línea

        assert len(text) == 502, _("The type 2 record must be 502 characters long")
        return text


    def _get_formatted_partner_refund(self, report, refund_record):
        """
        Returns a type 2, refund record

        Format of the record:
            Tipo registro 2
            Posiciones  Naturaleza      Descripción
            1           Numérico        Tipo de Registro            Constante = '2'
            2-4         Numérico        Modelo Declaración          Constante = '349'
            5-8         Numérico        Ejercicio
            9-17        Alfanumérico    NIF del declarante
            18-75       Blancos         ----------------------------------------
            76-92       Alfanumérico    NIF operador Intracomunitario
            - 76-77       Alfanumérico    Codigo de Pais
            - 78-92       Alfanumérico    NIF
            93-132      Alfanumérico    Apellidos y nombre o razón social del operador intracomunitario
            133         Alfanumérico    Clave de operación
            134-146     Blancos         ----------------------------------------
            147-178     Alfanumérico    Rectificaciones
            - 147-150     Numérico        Ejercicio
            - 151-152     Alfanumérico    Periodo
            - 153-165     Numérico        Base Imponible rectificada
              - 153-163     Numérico        Base Imponible (parte entera)
              - 164-165     Numérico        Base Imponible (parte decimal)
            166-178     Numérico        Base imponible declarada anteriormente
            - 166-176     Numérico        Base imponible declarada anteriormente (parte entera)
            - 177-176     Numérico        Base imponible declarada anteriormente (parte decimal)
            179-500     Blancos         ----------------------------------------
        """

        assert report, 'No AEAT 349 Report defined'
        assert refund_record, 'No Refund record defined'

        text = ''
        period = refund_record.period_selection == 'MO' and refund_record.month_selection or refund_record.period_selection

        text += '2'                                                             # Tipo de registro
        text += '349'                                                           # Modelo de declaración
        text += self._formatNumber(report.fiscalyear_id.code, 4)                # Ejercicio
        text += self._formatString(report.company_vat, 9)                       # NIF del declarante
        text += 58*' '                                                          # Blancos        
        text += self._formatString(refund_record.partner_id.vat, 17)            # NIF del operador intracomunitario
        text += self._formatString(refund_record.partner_id.name, 40)           # Apellidos y nombre o razón social del operador intracomunitario
        text += self._formatString(refund_record.operation_key, 1)              # Clave de operación
        text += 13*' '                                                          # Blancos
        text += self._formatNumber(refund_record.fiscalyear_id.code, 4)         # Ejercicio (de la rectificación)
        text += self._formatString(period, 2)                                   # Periodo (de la rectificación)
        text += self._formatNumber(refund_record.total_operation_amount, 11, 2) # Base imponible de la rectificación
        text += self._formatNumber(refund_record.total_origin_amount, 11, 2)    # Base imponible declarada anteriormente
        text += 322*' '                                                         # Blancos
        text +='\r\n'                                                           # Retorno de carro + Salto de línea

        assert len(text) == 502, _("The type 2 record must be 502 characters long")
        return text


    def _get_formated_other_records(self, report):
        file_contents = ''
        for refund_record in report.partner_refund_ids:
            file_contents += self._get_formatted_partner_refund(report, refund_record)
        
        return file_contents
    

    def _export_boe_file(self, cr, uid, ids, object_to_export, model=None, context=None):
        return super(l10n_es_aeat_mod349_export_to_boe, self)._export_boe_file(cr, uid, ids, object_to_export, model='349')

l10n_es_aeat_mod349_export_to_boe()
