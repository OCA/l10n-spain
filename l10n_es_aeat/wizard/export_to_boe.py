# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
#        Luis Manuel Angueira Blanco (Pexego)
#
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com) All Rights Reserved
#        Migración a OpenERP 7.0
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


import base64
import time

from openerp.osv import orm, fields
from openerp.tools.translate import _
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT 


class l10n_es_aeat_report_export_to_boe(orm.TransientModel):
    _name = "l10n.es.aeat.report.export_to_boe"
    _description = "Export Report to BOE Format"
    
    
    ########################
    ### HELPER FUNCTIONS ###
    ########################
    def _formatString(self, text, length, fill=' ', align='<'):
        """
        Formats the string into a fixed length ASCII (iso-8859-1) record.

        Note:
            'Todos los campos alfanuméricos y alfabéticos se presentarán 
            alineados a la izquierda y rellenos de blancos por la derecha,
            en mayúsculas sin caracteres especiales, y sin vocales acentuadas.
            Para los caracteres específicos del idioma se utilizará la
            codificación ISO-8859-1. De esta forma la letra “Ñ” tendrá el
            valor ASCII 209 (Hex. D1) y la “Ç”(cedilla mayúscula) el valor
            ASCII 199 (Hex. C7).'
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
        #ascii_string = '{0:{1}{2}{3}s}'.format(ascii_string, fill, align,
        # length) #for python >= 2.6
        if align == '<':
            ascii_string = str(ascii_string) + \
            (length-len(str(ascii_string)))*fill
        elif align == '>':
            ascii_string = (length-len(str(ascii_string)))* \
            fill + str(ascii_string)
        else:
            assert False, _('Wrong aling option. It should be < or >')

        # Sanity-check
        assert len(ascii_string) == length, \
            _("The formated string must match the given length")
        # Return string
        return ascii_string


    def _formatNumber(self, number, int_length, dec_length=0,
                      include_sign=False):
        """
        Formats the number into a fixed length ASCII (iso-8859-1) record.
        Note:
            'Todos los campos numéricos se presentarán alineados a la derecha
            y rellenos a ceros por la izquierda sin signos y sin empaquetar.'
            (http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)
        """
        #
        # Separate the number parts (-55.23 => int_part=55,
        # dec_part=0.23, sign='N')
        #
        if number == '':
            number = 0.0

        number = float(number)
        sign = number >= 0 and ' ' or 'N'
        number = abs(number)
        int_part = int(number)

        ##
        ## Format the string
        ascii_string = ''
        if include_sign:
            ascii_string += sign
            
        if dec_length > 0:
            ascii_string += '%0*.*f' % (int_length+ \
                                        dec_length+1,dec_length, number)
            ascii_string = ascii_string.replace('.','')
        elif int_length > 0:
            ascii_string += '%.*d' % (int_length, int_part)
            
        # Sanity-check
        assert len(ascii_string) == (include_sign and 1 or 0) + int_length + \
            dec_length, _("The formated string must match the given length")
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

        assert model , u"AEAT Model is necessary"

        file_contents = ''

        ##
        ## Add header record
        file_contents += self._get_formated_declaration_record(report)

        ##
        ## Add the partner records
        for partner_record in report.partner_record_ids:
            file_contents += self._get_formated_partner_record(report,
                                                               partner_record)

        ##
        ## Adds other fields
        file_contents += self._get_formated_other_records(report)

        ##
        ## Generate the file and save as attachment
        file = base64.encodestring(file_contents)

        file_name = _("%s_report_%s.txt") % \
            (model,time.strftime(_(DEFAULT_SERVER_DATE_FORMAT)))
        
        # Delete old files
        obj_attachment = self.pool.get('ir.attachment')
        attachment_ids = obj_attachment.search(
           cr, uid, [('name', '=', file_name),
                     ('res_model', '=', report._model._name)]
           )
        if len(attachment_ids):
            obj_attachment.unlink(cr, uid, attachment_ids)
            
        attach_id = self.pool.get("ir.attachment").create(cr, uid, {
            "name" : file_name,
            "datas" : file,
            "datas_fname" : file_name,
            "res_model" : "l10n.es.aeat.mod%s.report" % model,
            "res_id" : ids and ids[0]
        }, context=context)
        
        mod_obj = self.pool.get(report._model._name)
        mod_obj.write(cr,uid,[report.id],{'attach_id':attach_id},context)
        
        return True

l10n_es_aeat_report_export_to_boe()
