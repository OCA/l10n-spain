# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Export format BOE model 347 engine
#    Copyright (C) 2009 Asr Oss. All Rights Reserved
#    $Id$
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

"""
Export format BOE model 347 engine wizards
"""
__author__ = """Alejandro Sanchez Ramirez Asr Oss - alejandro@asr-oss.com
                Borja López Soilán (Pexego) - borjals@pexego.es"""


from tools.translate import _
import wizard
import pooler
import base64
import time


############################################################################
# Helper functions
############################################################################

def _formatString(text, length, fill=' ', align='<'):
    """
    Formats the string into a fixed lenght ASCII (iso-8859-1) record.

    Note:
        'Todos los campos alfanuméricos y alfabéticos se presentarán alineados a la izquierda y
        rellenos de blancos por la derecha, en mayúsculas sin caracteres especiales, y sin vocales acentuadas.
        Para los caracteres específicos del idioma se utilizará la codificación ISO-8859-1. De esta
        forma la letra “Ñ” tendrá el valor ASCII 209 (Hex. D1) y la “Ç”(cedilla mayúscula) el valor ASCII
        199 (Hex. C7).'
        (http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)
    """
    #
    # Turn text (probably unicode) into an ASCII (iso-8859-1) string
    #
    if isinstance(text, (unicode)):
        ascii_string = text.encode('iso-8859-1', 'ignore')
    else:
        ascii_string = str(text or '')
    # Cut the string if it is too long
    if len(ascii_string) > length:
        ascii_string = ascii_string[:lenght]
    # Format the string
    ascii_string = '{0:{1}{2}{3}s}'.format(ascii_string, fill, align, length)
    # Turn into uppercase
    return ascii_string.upper()
    #
    # Replace accents
    #
    replacements = [('Á', 'A'), ('É', 'E'), ('Í', 'I'), ('Ó', 'O'), ('Ú', 'U')]
    for orig, repl in replacements:
        ascii_string.replace(orig, repl)
    # Sanity-check
    assert len(ascii_string) == length, \
                        _("The formated string must match the given length")
    # Return string
    return ascii_string

def _formatNumber(number, int_lenght, dec_lenght=0, include_sign=False):
    """
    Formats the number into a fixed lenght ASCII (iso-8859-1) record.
    Note:
        'Todos los campos numéricos se presentarán alineados a la derecha
        y rellenos a ceros por la izquierda sin signos y sin empaquetar.'
        (http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)
    """
    #
    # Separate the number parts (-55.23 => int_part=55, dec_part=0.23, sign='N')
    #
    _number = float(number)
    int_part = int(_number)
    dec_part = int((_number % 1)*100)
    sign = _number > 0 and ' ' or 'N'
    #
    # Format the string
    #
    ascii_string = ''
    if include_sign:
        ascii_string += sign
    if int_lenght > 0:
        ascii_string += '{0:0>{1}}'.format(int_part, int_lenght)
    if dec_lenght > 0:
        ascii_string += '{0:0<{1}}'.format(dec_part, dec_lenght)
    # Sanity-check
    assert len(ascii_string) == (include_sign and 1 or 0) + int_lenght + dec_lenght, \
                        _("The formated string must match the given length")
    # Return the string
    return ascii_string

def _formatBoolean(value, yes='X', no=' '):
    """
    Formats a boolean value into a fixed lenght ASCII (iso-8859-1) record.
    """
    return value and yes or no


############################################################################
# Wizard
############################################################################

class wizard_export_boe(wizard.interface):
    """
    Wizard to export the 347 model report in BOE format.
    """

    ############################################################################
    # Forms
    ############################################################################

    _init_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="Export 347 in BOE format" colspan="4" width="400">
        <label string="This wizard will export the 347 report data to a BOE format file." colspan="4"/>
        <label string="" colspan="4"/>
        <label string="You may afterwards import this file into the AEAT help program." colspan="4"/>
    </form>"""

    _done_form = """<?xml version="1.0" encoding="utf-8"?>
    <form string="347 report exported in BOE format" colspan="4" width="400">
        <label string="The report file has been sucessfully generated." colspan="4"/>
        <label string="" colspan="4"/>
        <field name="file_name" nolabel="1"/>
        <field name="file" filename="file_name" nolabel="1"/>
        <label string="" colspan="4"/>
        <label string="You may now verify, print or upload the exported file using the AEAT help program available at:" colspan="4"/>
        <field name="aeat_program_download_url" widget="url" nolabel="1" colspan="4"/>
    </form>"""

    _done_fields = {
        'file' : { 'string': 'Exported file', 'type':'binary', 'readonly':True },
        'file_name': {'string': 'Exported file', 'type': 'char', 'size': 64, 'readonly':True},
        'aeat_program_download_url' : {'string': 'AEAT URL', 'type': 'char', 'size': 255 },
    }

    ############################################################################
    # Actions
    ############################################################################

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
        text += _formatString(report.fiscalyear_id.code, 4)   # Ejercicio
        text += _formatString(report.company_vat, 9)          # NIF del declarante
        text += _formatString(report.company_id.name, 40)     # Apellidos y nombre o razón social del declarante
        text += _formatString(report.support_type, 1)         # Tipo de soporte
        text += _formatString(report.contact_phone, 9)       # Persona de contacto (Teléfono)
        text += _formatString(report.contact_name, 40)        # Persona de contacto (Apellidos y nombre)
        text += _formatNumber(report.number, 13)              # Número identificativo de la declaración
        text += _formatString(report.type, 2)                 # Declaración complementaria o substitutiva
        text += _formatNumber(report.previous_number, 13)     # Número identificativo de la declaración anterior
        text += _formatNumber(report.total_partner_records, 9)          # Número total de personas y entidades
        text += _formatNumber(report.total_amount, 13, 2)               # Importe total de las operaciones
        text += _formatNumber(report.total_real_state_records, 9)       # Número total de inmuebles
        text += _formatNumber(report.total_real_state_amount, 13, 2)    # Importe total de las operaciones de arrendamiento
        text += 207*' '                                       # Blancos
        text += _formatString(report.representative_vat, 9)   # NIF del representante legal
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
            130-500 	Blancos
            488-500 	Sello electrónico 
        """
        text = ''

        text += '2'                                                     # Tipo de Registro
        text += '347'                                                   # Modelo Declaración
        text += _formatString(report.fiscalyear_id.code, 4)             # Ejercicio
        text += _formatString(report.company_vat, 9)                    # NIF del declarante
        text += _formatString(partner_record.partner_vat, 9)            # NIF del declarado
        text += _formatString(partner_record.representative_vat, 9)     # NIF del representante legal
        text += _formatString(partner_record.partner_id.name, 40)       # Apellidos y nombre, razón social o denominación del declarado
        text += 'D'                                                     # Tipo de hoja: Constante ‘D’.
        text += _formatNumber(partner_record.partner_state_code, 2)     # Código provincia
        text += _formatString(partner_record.partner_country_code, 2)   # Código país
        text += ' '                                                     # Blancos
        text += _formatString(partner_record.operation_key, 1)          # Clave de operación
        text += _formatNumber(partner_record.amount, 13, 2)             # Importe de las operaciones
        text += _formatBoolean(partner_record.insurance_operation)                      # Operación de seguro
        text += _formatBoolean(partner_record.bussiness_real_state_rent)                # Arrendamiento local negocio
        text += _formatNumber(partner_record.cash_amount, 13, 2)                        # Importe percibido en metálico
        text += _formatNumber(partner_record.real_state_transmissions_amount, 13, 2)    # Importe percibido por transmisiones de inmuebles sujetas a IVA
        text += 371*' '                                                 # Blancos
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
        text += _formatNumber(report.fiscalyear_id.code, 4)             # Ejercicio
        text += _formatString(report.company_vat, 9)                    # NIF del declarante
        text += _formatString(partner_record.partner_vat, 9)            # NIF del declarado
        text += _formatString(partner_record.representative_vat, 9)     # NIF del representante legal
        text += _formatString(partner_record.partner_id.name, 40)       # Apellidos y nombre, razón social o denominación del declarado
        text += 'I'                                                     # Tipo de hoja: Constante ‘I’.
        text += 23*''                                                   # Blancos
        text += _formatNumber(partner_record.real_state_amount, 13, 2)  # Importe de las operaciones
        text += _formatNumber(partner_record.real_state_situation, 1)   # Situación del inmueble
        text += _formatString(partner_record.real_state_reference, 25)  # Referencia catastral
        text += _formatString(partner_record.real_state_address_type, 5)        # TIPO DE VÍA
        text += _formatString(partner_record.real_state_address, 50)            # NOMBRE VÍA PUBLICA
        text += _formatString(partner_record.real_state_number_type, 3)         # TIPO DE NUMERACIÓN
        text += _formatString(partner_record.real_state_number, 5)              # NUMERO DE CASA
        text += _formatString(partner_record.real_state_number_calification, 3) # CALIFICADOR DEL NUMERO
        text += _formatString(partner_record.real_state_block, 3)               # BLOQUE
        text += _formatString(partner_record.real_state_portal, 3)              # PORTAL
        text += _formatString(partner_record.real_state_stairway, 3)            # ESCALERA
        text += _formatString(partner_record.real_state_floor, 3)               # PLANTA O PISO
        text += _formatString(partner_record.real_state_door, 3)                # PUERTA
        text += _formatString(partner_record.real_state_complement, 40)         # COMPLEMENTO
        text += _formatString(partner_record.real_state_city, 30)               # LOCALIDAD O POBLACIÓN
        text += _formatString(partner_record.real_state_township, 30)           # MUNICIPIO
        text += _formatString(partner_record.real_state_township_code, 5)       # CODIGO DE MUNICIPIO
        text += _formatString(partner_record.real_state_state_code, 2)          # CODIGO PROVINCIA
        text += _formatString(partner_record.real_state_postal_code, 5)         # CODIGO POSTAL
        text += 167*' '                                                 # Blancos
        text += '\r\n'                                                  # Sello electrónico

        assert len(text) == 502, _("The type 2-I record (real state) must be 502 characters long")
        return text
    

    def _export_boe_file(self, cr, uid, data, context):
        """
        Action that exports the data into a BOE formated text file.
        """

        pool = pooler.get_pool(cr.dbname)
        report = pool.get('l10n.es.aeat.mod347.report').browse(cr, uid, data['id'], context=context)

        file_contents = ''

        # Add the header record
        file_contents += self._get_formated_declaration_record(report)

        #
        # Add the partner records
        #
        for partner_record in report.partner_record_ids:
            file_contents += self._get_formated_partner_record(report, partner_record)

        #
        # Add the real state records
        #
        for real_state_record in report.real_state_record_ids:
            file_contents += self._get_formated_real_state_record(report, real_state_record)

        #
        # Generate the file
        #
        file = base64.encodestring(file_contents)
        file_name = _('347_report_%s.txt') %  time.strftime(_('%Y-%m-%d'))

        #
        # Return the data
        #
        return {
            'file': file,
            'file_name': file_name,
            'aeat_program_download_url': "http://www.aeat.es/wps/portal/ProgramaAyuda?channel=e5b22fc8ebd4f010VgnVCM1000004ef01e0a____&ver=L&site=56d8237c0bc1ff00VgnVCM100000d7005a80____"
        }

    ############################################################################
    # States
    ############################################################################

    states = {
        'init': {
            'actions': [],
            'result': {'type':'form', 'arch': _init_form, 'fields': {}, 'state':[('end', 'Cancel', 'gtk-cancel', True), ('export', 'Export', 'gtk-apply', True)]}
        },
        'export': {
            'actions': [_export_boe_file],
            'result': {'type': 'form', 'arch': _done_form, 'fields': _done_fields, 'state':[('end','Done', 'gtk-ok', True)]}
        }
    }

wizard_export_boe('l10n_es_aeat_mod347.wizard_export_boe')

