# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C)
#        2004-2011: Pexego Sistemas Informáticos. (http://pexego.es)
#        2013:      Top Consultant Software Creations S.L.
#                   (http://www.topconsultant.es/)
#        2014:      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                   Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
#    Autores originales: Luis Manuel Angueira Blanco (Pexego)
#                        Omar Castiñeira Saavedra(omar@pexego.es)
#    Migración OpenERP 7.0: Ignacio Martínez y Miguel López.
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
from openerp import api, fields, models, _


class Mod349ExportToBoe(models.TransientModel):
    _inherit = "l10n.es.aeat.report.export_to_boe"
    _name = "l10n.es.aeat.mod349.export_to_boe"
    _description = "Export AEAT Model 349 to BOE format"

    @api.multi
    def _get_company_name_with_title(self, company_obj):
        """Returns company name with title."""
        if company_obj.partner_id and company_obj.partner_id.title:
            return company_obj.name + ' ' + \
                company_obj.partner_id.title.name.capitalize()
        return company_obj.name

    @api.multi
    def _get_formatted_declaration_record(self, report):
        """Returns a type 1, declaration/company, formated record.

            · All amounts must be positives
            · Numeric fields with no data must be filled with zeros
            · Alfanumeric/Alfabetic fields with no data must be filled with
              empty spaces
            · Numeric fields must be right aligned and filled with zeros on
              the left
            · Alfanumeric/Alfabetic fields must be uppercase left aligned,
              filled with empty spaces on right side. No special characters
              allowed unless specified in field description

        Format of the record:
            Tipo registro 1 – Registro de declarante:
            Posiciones  Naturaleza      Descripción
            1           Numérico        Tipo de Registro      Constante = '1'
            2-4         Numérico        Modelo Declaración    Constante = '349'
            5-8         Numérico        Ejercicio
            9-17        Alfanumérico    NIF del declarante
            18-57       Alfanumérico    Apellidos y nombre o razón social del
                                        declarante
            58          Alfabético      Tipo de soporte
            59-67       Numérico (9)    Teléfono contacto
            68-107      Alfabético      Apellidos y nombre contacto
            108-120     Numérico        Número identificativo de la declaración
            121-122     Alfabético      Declaración complementaria o
                                        substitutiva
            123-135     Numérico        Número identificativo de la declaración
                                        anterior
            136-137     Alfanumérico    Período
            138-146     Numérico        Número total de operadores
                                        intracomunitarios
            147-161     Numérico        Importe de las operaciones
                                        intracomunitarias
            147-159     Numérico        Importe de las operaciones
                                        intracomunitarias (parte entera)
            160-161     Numérico        Importe de las operaciones
                                        intracomunitarias (parte decimal)
            162-170     Numérico        Número total de operadores
                                        intracomunitarios con rectificaciones
            171-185     Numérico        Importe total de las rectificaciones
            171-183     Numérico        Importe total de las rectificaciones
                                        (parte entera)
            184-185     Numérico        Importe total de las rectificaciones
                                        (parte decimal)
            186         Alfabético      Indicador cambio periodicidad en la
                                        obligación a declarar (X o '')
            187-390     Blancos         ---------------------------------------
            391-399     Alfanumérico    NIF del representante legal
            400-487     Blancos         ---------------------------------------
            488-500     Sello electrónico
        """
        assert report, 'No Report defined'
        text = super(Mod349ExportToBoe,
                     self)._get_formatted_declaration_record(report)
        text += self._formatString(report.period_type, 2)  # Período
        # Número total de operadores intracomunitarios
        text += self._formatNumber(report.total_partner_records, 9)
        # Importe total de las operaciones intracomunitarias (parte entera)
        text += self._formatNumber(report.total_partner_records_amount, 13, 2)
        # Número total de operadores intracomunitarios con rectificaciones
        text += self._formatNumber(report.total_partner_refunds, 9)
        # Importe total de las rectificaciones
        text += self._formatNumber(report.total_partner_refunds_amount, 13, 2)
        # Indicador cambio periodicidad en la obligación a declarar
        text += self._formatBoolean(report.frequency_change)
        text += 204 * ' '  # Blancos
        # NIF del representante legal
        text += self._formatString(report.representative_vat, 9)
        # text += 9*' '
        text += 88 * ' '  # Blancos
        text += 13 * ' '  # Sello electrónico
        text += '\r\n'  # Retorno de carro + Salto de línea
        assert len(text) == 502, \
            _("The type 1 record must be 502 characters long")
        return text

    @api.multi
    def _get_formatted_main_record(self, report):
        file_contents = ''
        for partner_record in report.partner_record_ids:
            file_contents += self._get_formated_partner_record(
                report, partner_record)
        for refund_record in report.partner_refund_ids:
            file_contents += self._get_formatted_partner_refund(
                report, refund_record)
        return file_contents

    @api.multi
    def _get_formated_partner_record(self, report, partner_record):
        """Returns a type 2, partner record

        Format of the record:
            Tipo registro 2
            Posiciones  Naturaleza      Descripción
            1           Numérico        Tipo de Registro       Constante = '2'
            2-4         Numérico        Modelo Declaración     onstante = '349'
            5-8         Numérico        Ejercicio
            9-17        Alfanumérico    NIF del declarante
            18-75       Blancos         ---------------------------------------
            76-92       Alfanumérico    NIF operador Intracomunitario
            76-77       Alfanumérico    Codigo de País
            78-92       Alfanumérico    NIF
            93-132      Alfanumérico    Apellidos y nombre o razón social del
                                        operador intracomunitario
            133         Alfanumérico    Clave de operación
            134-146     Numérico        Base imponible
            134-144     Numérico        Base imponible (parte entera)
            145-146     Numérico        Base imponible (parte decimal)
            147-500     Blancos         ---------------------------------------
        """
        assert report, 'No AEAT 349 Report defined'
        assert partner_record, 'No Partner record defined'
        text = ''
        # Formateo de algunos campos (debido a que pueden no ser correctos)
        # NIF : Se comprueba que no se incluya el código de pais
        company_vat = report.company_vat
        if len(report.company_vat) > 9:
            company_vat = report.company_vat[2:]
        text += '2'  # Tipo de registro
        text += '349'  # Modelo de declaración
        date_start = fields.Date.from_string(report.periods[:1].date_start)
        text += self._formatNumber(date_start.year, 4)  # Ejercicio
        text += self._formatString(company_vat, 9)  # NIF del declarante
        text += 58 * ' '  # Blancos
        # NIF del operador intracomunitario
        text += self._formatString(partner_record.partner_vat, 17)
        # Apellidos y nombre o razón social del operador intracomunitario
        text += self._formatString(partner_record.partner_id.name, 40)
        # Clave de operación
        text += self._formatString(partner_record.operation_key, 1)
        # Base imponible (parte entera)
        text += self._formatNumber(partner_record.total_operation_amount, 11,
                                   2)
        text += 354 * ' '  # Blancos
        text += '\r\n'  # Retorno de carro + Salto de línea
        assert len(text) == 502, \
            _("The type 2 record must be 502 characters long")
        return text

    @api.multi
    def _get_formatted_partner_refund(self, report, refund_record):
        """Returns a type 2, refund record

        Format of the record:
            Tipo registro 2
            Posiciones  Naturaleza      Descripción
            1           Numérico        Tipo de Registro      Constante = '2'
            2-4         Numérico        Modelo Declaración    Constante = '349'
            5-8         Numérico        Ejercicio
            9-17        Alfanumérico    NIF del declarante
            18-75       Blancos         ---------------------------------------
            76-92       Alfanumérico    NIF operador Intracomunitario
            76-77       Alfanumérico    Codigo de Pais
            78-92       Alfanumérico    NIF
            93-132      Alfanumérico    Apellidos y nombre o razón social del
                                        operador intracomunitario
            133         Alfanumérico    Clave de operación
            134-146     Blancos         ---------------------------------------
            147-178     Alfanumérico    Rectificaciones
            147-150     Numérico        Ejercicio
            151-152     Alfanumérico    Periodo
            153-165     Numérico        Base Imponible rectificada
            153-163     Numérico        Base Imponible (parte entera)
            164-165     Numérico        Base Imponible (parte decimal)
            166-178     Numérico        Base imponible declarada anteriormente
            166-176     Numérico        Base imponible declarada anteriormente
                                        (parte entera)
            177-176     Numérico        Base imponible declarada anteriormente
                                        (parte decimal)
            179-500     Blancos         ---------------------------------------
        """
        assert report, 'No AEAT 349 Report defined'
        assert refund_record, 'No Refund record defined'
        text = ''
        text += '2'  # Tipo de registro
        text += '349'  # Modelo de declaración
        date_start = fields.Date.from_string(report.periods[:1].date_start)
        text += self._formatNumber(date_start.year, 4)  # Ejercicio
        text += self._formatString(report.company_vat, 9)  # NIF del declarante
        text += 58 * ' '   # Blancos
        # NIF del operador intracomunitario
        text += self._formatString(refund_record.partner_id.vat, 17)
        # Apellidos y nombre o razón social del operador intracomunitario
        text += self._formatString(refund_record.partner_id.name, 40)
        # Clave de operación
        text += self._formatString(refund_record.operation_key, 1)
        text += 13 * ' '  # Blancos
        # Ejercicio (de la rectificación)
        date_start = fields.Date.from_string(
            refund_record.fiscalyear_id.date_start)
        text += self._formatNumber(date_start.year, 4)
        # Periodo (de la rectificación)
        text += self._formatString(refund_record.period_type, 2)
        # Base imponible de la rectificación
        text += self._formatNumber(refund_record.total_operation_amount, 11, 2)
        # Base imponible declarada anteriormente
        text += self._formatNumber(refund_record.total_origin_amount, 11, 2)
        text += 322 * ' '  # Blancos
        text += '\r\n'  # Retorno de carro + Salto de línea
        assert len(text) == 502, _("The type 2 record must be 502 characters "
                                   "long")
        return text
