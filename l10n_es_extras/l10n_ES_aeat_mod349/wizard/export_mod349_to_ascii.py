# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Informáticos. All Rights Reserved
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


import wizard
import pooler
import base64
import time

from tools.translate import _


def _formatString(text, length, fill=' ', align='<'):
    """
    Formats the string into a fixed length ASCII (iso-8859-1) record.

    Note:
        'Todos los campos alfanuméricos y alfabéticos se presentarán alineados a la izquierda y
        rellenos de blancos por la derecha, en mayúsculas sin caracteres especiales, y sin vocales acentuadas.
        Para los caracteres específicos del idioma se utilizará la codificación ISO-8859-1. De esta
        forma la letra “Ñ” tendrá el valor ASCII 209 (Hex. D1) y la “Ç”(cedilla mayúscula) el valor ASCII
        199 (Hex. C7).'
    """
    if not text:
        return fill*length

    #
    # Replace accents
    #
    replacements = [
        (u'Á', 'A'),(u'á', 'A'),
        (u'É', 'E'),(u'é', 'E'),
        (u'Í', 'I'),(u'í', 'I'),
        (u'Ó', 'O'),(u'ó', 'O'),
        (u'Ú', 'U'),(u'ú', 'U'),
        (u'Ä', 'A'),(u'ä', 'A'),
        (u'Ë', 'E'),(u'ë', 'E'),
        (u'Ï', 'I'),(u'ï', 'I'),
        (u'Ö', 'O'),(u'ö', 'O'),
        (u'Ü', 'U'),(u'ü', 'U'),
        (u'À', 'A'),(u'à', 'A'),
        (u'È', 'E'),(u'è', 'E'),
        (u'Ì', 'I'),(u'ì', 'I'),
        (u'Ò', 'O'),(u'ò', 'O'),
        (u'Ù', 'U'),(u'ù', 'U'),
        (u'Â', 'A'),(u'â', 'A'),
        (u'Ê', 'E'),(u'ê', 'E'),
        (u'Î', 'I'),(u'î', 'I'),
        (u'Ô', 'O'),(u'ô', 'O'),
        (u'Û', 'U'),(u'û', 'U')]

    for orig, repl in replacements:
        text = text.replace(orig, repl)

    #
    # String uppercase
    #
    text = text.upper()
    
    #
    # Turn text (probably unicode) into an ASCII (iso-8859-1) string
    #
    if isinstance(text, (unicode)):
        ascii_string = text.encode('iso-8859-1', 'ignore')
    else:
        ascii_string = str(text or '')
    # Cut the string if it is too long
    if len(ascii_string) > length:
        ascii_string = ascii_string[:length]
    # Format the string
    #ascii_string = '{0:{1}{2}{3}s}'.format(ascii_string, fill, align, length) #for python >= 2.6
    if align == '<':
        ascii_string = str(ascii_string) + (length-len(str(ascii_string)))*fill
    elif align == '>':
        ascii_string = (length-len(str(ascii_string)))*fill + str(ascii_string)
    else:
        assert False, _('Wrong aling option. It should be < or >')

    # Sanity-check
    assert len(ascii_string) == length, \
                        _("The formated string must match the given length")
    # Return string
    return ascii_string


def _formatNumber(number, int_length, dec_length=0, include_sign=False):
    """
    Formats the number into a fixed length ASCII (iso-8859-1) record.
    Note:
        'Todos los campos numéricos se presentarán alineados a la derecha
        y rellenos a ceros por la izquierda sin signos y sin empaquetar.'
        (http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)
    """
    #
    # Separate the number parts (-55.23 => int_part=55, dec_part=0.23, sign='N')
    #
    if number == '':
        number = 0.0
    number = float(number)
    sign = number > 0 and ' ' or 'N'
    number = abs(number)
    int_part = int(number)
    dec_part = int(round((number % 1.0),2)*100.0)
    
    #
    # Format the string
    #
    ascii_string = ''
    if include_sign:
        ascii_string += sign
    if int_length > 0:
        ascii_string += '%.*d' % (int_length, int_part)
    if dec_length > 0:
        ascii_string += str(dec_part)+(dec_length-len(str(dec_part)))*'0'
    # Sanity-check
    assert len(ascii_string) == (include_sign and 1 or 0) + int_length + dec_length, \
                        _("The formated string must match the given length")
    # Return the string
    return ascii_string


def _formatBoolean(value, yes='X', no=' '):
    """
    Formats a boolean value into a fixed length ASCII (iso-8859-1) record.
    """
    return value and yes or no


class wizard_export_mod349_to_ascii(wizard.interface):

    #############
    ### FORMS ###
    #############
    INIT_FORM = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Export 349 in BOE format" colspan="4" width="400">
        <label string="This wizard will export the 349 report data to a BOE format file." colspan="4"/>
        <label string="" colspan="4"/>
        <label string="You may afterwards import this file into the AEAT help program." colspan="4"/>
    </form>"""

    DONE_FORM = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Export 349 in BOE format" colspan="4" width="400">
        <label string="The report file has been successfully generated" colspan="4"/>
        <label string="" colspan="4"/>
        <field name="file_name" nolabel="1"/>
        <field name="file" filename="file_name" nolabel="1"/>
        <label string="" colspan="4"/>
        <label string="You may now verify, print or upload the exported file using the AEAT help program available at:" colspan="4"/>
        <field name="aeat_program_download_url" widget="url" nolabel="1" colspan="4"/>
    </form>"""



    ###################
    ### DONE FIELDS ###
    ###################
    DONE_FIELDS = {
        'file' : {
            'string' : 'Exported file',
            'type' : 'binary',
            'readonly' : True
        },
        'file_name' : {
            'string' : 'Exported file',
            'type' : 'char',
            'size' : 64,
            'readonly' : True
        },
        'aeat_program_download_url' : {
            'string' : 'AEAT URL',
            'type' : 'char',
            'size' : 255
        }
    }


    #################
    ### FUNCTIONS ###
    #################
    def _get_company_name_with_title(self, company_obj):
        """
        Returns company name with title
        """
        if company_obj.partner_id and \
            company_obj.partner_id.title:
                return company_obj.name + ' ' + company_obj.partner_id.title.capitalize()

        return company_obj.name


    def _get_formatted_report(self, report):
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
        
        text = ''                                                       ## Empty text
            
        text += '1'                                                         # Tipo de Registro
        text += '349'                                                       # Modelo Declaración
        text += _formatNumber(fiscal_year, 4)                               # Ejercicio
        text += _formatString(report.company_vat, 9)                        # NIF del declarante
        text += _formatString(company_name, 40)                             # Apellidos y nombre o razón social del declarante
        text += _formatString(report.support_type, 1)                       # Tipo de soporte
        text += _formatNumber(report.contact_phone.replace(' ', ''), 9)                      # Persona de contacto (Teléfono)
        text += _formatString(report.contact_name, 40)                      # Persona de contacto (Apellidos y nombre)
        text += _formatNumber(report.number, 13)                            # Número identificativo de la declaración
        text += _formatString(report.type, 2).replace('N', ' ')             # Declaración complementaria o substitutiva
        text += _formatNumber(report.previous_number, 13)                   # Número identificativo de la declaración anterior
        text += _formatString(period, 2)                                 # Período
        text += _formatNumber(report.total_partner_records, 9)              # Número total de operadores intracomunitarios
        text += _formatNumber(report.total_partner_records_amount, 13, 2)   # Importe total de las operaciones intracomunitarias (parte entera)
        text += _formatNumber(report.total_partner_refunds, 9)              # Número total de operadores intracomunitarios con rectificaciones
        text += _formatNumber(report.total_partner_refunds_amount, 13, 2)   # Importe total de las rectificaciones
        text += _formatBoolean(report.frequency_change)                     # Indicador cambio periodicidad en la obligación a declarar
        text += 204*' '                                                     # Blancos
        text += _formatString(report.representative_vat, 9)                 # NIF del representante legal
        text += 88*' '                                                      # Blancos
        text += 13*' '                                                      # Sello electrónico
        text += '\r\n'                                                      # Retorno de carro + Salto de línea

        assert len(text) == 502, _("The type 1 record must be 502 characters long")
        return text


    def _get_formatted_partner_record(self, report, partner_record):
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

        text += '2'                                                             # Tipo de registro
        text += '349'                                                           # Modelo de declaración
        text += _formatNumber(fiscal_year, 4)                                   # Ejercicio
        text += _formatString(company_vat, 9)                                   # NIF del declarante
        text += 58*' '                                                          # Blancos
        text += _formatString(partner_record.partner_vat[:2], 2)             # NIF del operador intracomunitario (código del país)
        text += _formatString(partner_record.partner_vat[2:], 15)            # NIF del operador intracomunitario (NIF)
        text += _formatString(partner_record.partner_id.name, 40)               # Apellidos y nombre o razón social del operador intracomunitario
        text += _formatString(partner_record.operation_key, 1)                  # Clave de operación
        text += _formatNumber(partner_record.total_operation_amount, 11, 2)     # Base imponible (parte entera)

        text += 354*' '                                                         # Blancos
        text +='\r\n'                                                           # Retorno de carro + Salto de línea

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

        text += '2'                                                         # Tipo de registro
        text += '349'                                                       # Modelo de declaración
        text += _formatNumber(report.fiscalyear_id.code, 4)                 # Ejercicio
        text += _formatString(report.company_vat, 9)                        # NIF del declarante
        text += 58*' '                                                      # Blancos
        text += _formatString(refund_record.partner_id.vat, 17)             # NIF del operador intracomunitario
        text += _formatString(refund_record.partner_id.name, 40)            # Apellidos y nombre o razón social del operador intracomunitario
        text += _formatString(refund_record.operation_key, 1)               # Clave de operación
        text += 13*' '                                                      # Blancos
        text += _formatNumber(refund_record.fiscalyear_id.code, 4)          # Ejercicio (de la rectificación)
        text += _formatString(period, 2)                                    # Periodo (de la rectificación)
        text += _formatNumber(refund_record.total_operation_amount, 11, 2)   # Base imponible de la rectificación
        text += _formatNumber(refund_record.total_origin_amount, 11, 2)      # Base imponible declarada anteriormente
        text += 322*' '                                                     # Blancos
        text +='\r\n'                                                       # Retorno de carro + Salto de línea

        assert len(text) == 502, _("The type 2 record must be 502 characters long")
        return text


    def _export_mod349_to_ascii(self, cr, uid, data, context=None):
        """
        Export an AEAT 349 Report to ASCII. Some facts:
        · Must be in ISO-8859-1
        · All numeric fields must be on right side, filled with zeros on the left
          with no signs, no packaging
        
        """
        if context is None:
            context = {}

        pool = pooler.get_pool(cr.dbname)
        report_facade = pool.get('l10n.es.aeat.mod349.report')
        report = report_facade.browse(cr, uid, data['id'], context=context)

        file_contents = ''

        ##
        ## HEADER (Declaration report)
        ##
        file_contents += self._get_formatted_report(report)

        ##
        ## Record for each partner record
        ##
        for partner_record in report.partner_record_ids:
            file_contents += self._get_formatted_partner_record(report, partner_record)

        ##
        ## Record for each refund record
        ##
        for refund_record in report.partner_refund_ids:
            file_contents += self._get_formatted_partner_refund(report, refund_record)


        ##
        ## Generate file and save as attachment
        ##
        file = base64.encodestring(file_contents)
        file_name = _('349_report_%s.txt') %  time.strftime(_('%Y-%m-%d %H-%M-%S'))
        pool.get('ir.attachment').create(cr, uid, {
            'name': _('349 report %s') %  time.strftime(_('%Y-%m-%d %H-%M-%S')),
            'datas': file,
            'datas_fname': file_name,
            'res_model': 'l10n.es.aeat.mod349.report',
            'res_id': report.id,
            }, context=context)

        #
        # Return the data
        #
        return {
            'file': file,
            'file_name': file_name,
            'aeat_program_download_url': "http://www.aeat.es/wps/portal/ProgramaAyuda?channel=e5b22fc8ebd4f010VgnVCM1000004ef01e0a____&ver=L&site=56d8237c0bc1ff00VgnVCM100000d7005a80____"
        }

            

    ##############
    ### STATES ###
    ##############
    states = {
        'init' : {
            'actions' : [],
            'result' : {
                'type' : 'form',
                'arch' : INIT_FORM,
                'fields' : {},
                'state' : [
                    ('end', 'Cancel', 'gtk-cancel', True),
                    ('export', 'Export', 'gtk-go-forward', True)]
            }
        },
        'export' : {
            'actions' : [_export_mod349_to_ascii],
            'result' : {
                'type' : 'form',
                'arch' : DONE_FORM,
                'fields' : DONE_FIELDS,
                'state' : [('end', 'Done', 'gtk-ok', True)]
            }
        }
    }
    


wizard_export_mod349_to_ascii('l10n_ES_aeat_mod349.export_mod349_to_ascii')
