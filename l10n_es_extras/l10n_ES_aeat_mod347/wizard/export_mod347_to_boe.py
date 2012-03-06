# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2010 Pexego Sistemas Inform�ticos. All Rights Reserved
#    Copyright (C) 2012
#        NaN·Tic  (http://www.nan-tic.com) All Rights Reserved
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
import time
import base64
import unicodedata


def unaccent(text):
    if isinstance( text, str ):
        text = unicode( text, 'utf-8' )
    return unicodedata.normalize('NFKD', text ).encode('ASCII', 'ignore')

class l10n_es_aeat_mod347_export_to_boe(osv.osv_memory):

    
    _name = "l10n.es.aeat.mod347.export_to_boe"
    _description = "Export AEAT Model 347 to BOE format"

    
    
    ########################
    ### HELPER FUNCTIONS ###
    ########################
    def _formatString(self, text, length, fill=' ', align='<'):
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

        #
        # String uppercase
        #
        text = unaccent( text.upper())

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

    def _formatNumber(self, number, int_length, dec_length=0, include_sign=False):
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
        if "%s.2f"%number == '0.00':
            sign =' '
        else:
            sign = number >= 0.0 and ' ' or 'N'
            
        number = abs(number)
        int_part = int(number)

        ##
        ## Format the string
        ascii_string = ''
        if include_sign:
            ascii_string += sign
            
        if dec_length > 0:
            ascii_string += '%0*.*f' % (int_length+dec_length+1,dec_length, number)
            ascii_string = ascii_string.replace('.','')
        elif int_length > 0:
            ascii_string += '%.*d' % (int_length, int_part)
            
        # Sanity-check
        assert len(ascii_string) == (include_sign and 1 or 0) + int_length + dec_length, \
                            _("The formated string must match the given length")
        # Return the string
        return ascii_string


    def _formatBoolean(self, value, yes='X', no=' '):
        """
        Formats a boolean value into a fixed length ASCII (iso-8859-1) record.
        """
        return value and yes or no


    #########################
    ### RECORDS FUNCTIONS ###
    #########################
    def _get_formated_declaration_record(self, report):
        return ''

    def _get_formated_partner_record(self, report, partner_record):
        return ''

    def _get_formated_other_records(self, report):
        return ''

    def _export_boe_file(self, cr, uid, ids, report, model=None, context=None):
        """
        Action that exports the data into a BOE formated text file
        """
        if context is None:
            context = {}


        file_contents = ''

        ##
        ## Add header record
        file_contents += self._get_formated_declaration_record(report)

        ##
        ## Add the partner records
        for partner_record in report.partner_record_ids:
            file_contents += self._get_formated_partner_record(report, partner_record)

        ##
        ## Adds other fields
        file_contents += self._get_formated_other_records(report)

        ##
        ## Generate the file and save as attachment
        file = base64.encodestring(file_contents)
        file_name = _("%s_report_%s.txt") % ('347', time.strftime(_("%Y-%m-%d")))
        self.pool.get("ir.attachment").create(cr, uid, {
            "name" : file_name,
            "datas" : file,
            "datas_fname" : file_name,
            "res_model" : "l10n.es.aeat.mod347.report",
            "res_id" : ids and ids[0] or ''
        }, context=context)

    
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
        text += self._formatNumber(report.total_amount, 13, 2,True)               # Importe total de las operaciones
        text += self._formatNumber(report.total_real_state_records, 9)       # Número total de inmuebles
        text += self._formatNumber(report.total_real_state_amount, 13, 2)    # Importe total de las operaciones de arrendamiento
        text += 206*' '                                       # Blancos
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
            83-98 	Importe de las operaciones
            98          Operación de seguro
            99          Arrendamiento local negocio
            100-114 	Importe percibido en metálico
            115-129 	Importe percibido por transmisiones de inmuebles sujetas a IVA
            130-134     Año de devengo de las operaciones en efectivo
            135-151     Importe de las operaciones del primer trimestre
            151-167     Importe percibido por transmisiones de inmuebles sujates a Iva Primer Trimestre
            168-183     Importe de las operaciones del Segundo trimestre
            183-199     Importe percibido por transmisiones de inmuebles sujates a Iva segundo Trimestre
            200-215     Importe de las operaciones del tercer trimestre
            215-231     Importe percibido por transmisiones de inmuebles sujates a Iva tercer Trimestre
            231-247     Importe de las operaciones del quarto trimestre
            247-263     Importe percibido por transmisiones de inmuebles sujates a Iva quarto Trimestre
            264-500 	Blancos
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
        text += self._formatNumber(partner_record.amount, 13, 2,True)             # Importe de las operaciones
        text += self._formatBoolean(partner_record.insurance_operation)                      # Operación de seguro
        text += self._formatBoolean(partner_record.bussiness_real_state_rent)                # Arrendamiento local negocio
        text += self._formatNumber(partner_record.cash_amount, 13, 2)                        # Importe percibido en metálico
        text += self._formatNumber(partner_record.real_state_transmissions_amount, 13, 2,True)    # Importe percibido por transmisiones de inmuebles sujetas a IVA
        text += partner_record.origin_fiscalyear_id and self._formatString(partner_record.origin_fiscalyear_id.code, 4) or 4*'0' #Año de devengo de las operaciones en efectivo
        text += self._formatNumber(partner_record.first_quarter,13,2,True)
        text += self._formatNumber(partner_record.first_quarter_real_state_transmission_amount,13,2,True)
        text += self._formatNumber(partner_record.second_quarter,13,2,True)
        text += self._formatNumber(partner_record.second_quarter_real_state_transmission_amount,13,2,True)
        text += self._formatNumber(partner_record.third_quarter,13,2,True)
        text += self._formatNumber(partner_record.third_quarter_real_state_transmission_amount,13,2,True)
        text += self._formatNumber(partner_record.fourth_quarter,13,2,True)
        text += self._formatNumber(partner_record.fourth_quarter_real_state_transmission_amount,13,2,True)        
        text += 237*' '                                                 # Blancos
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
    

l10n_es_aeat_mod347_export_to_boe()
