# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es)
#        Luis Manuel Angueira Blanco (Pexego)
#
#    Copyright (C) 2013
#        Ignacio Ibeas - Acysos S.L. (http://acysos.com)
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
from unidecode import unidecode


class L10nEsAeatReportExportToBoe(orm.TransientModel):
    _name = "l10n.es.aeat.report.export_to_boe"
    _description = "Export Report to BOE Format"

    _columns = {
        'name': fields.char('File name', readonly=True),
        'data': fields.binary('File', readonly=True),
        'state': fields.selection([('open', 'open'),  # open wizard
                                   ('get', 'get')]),  # get file
    }

    _defaults = {
        'state': 'open',
    }

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
            return fill * length
        # Replace accents and convert to upper
        text = unidecode(unicode(text))
        text = text.upper()
        ascii_string = text.encode('iso-8859-1')
        # Cut the string if it is too long
        if len(ascii_string) > length:
            ascii_string = ascii_string[:length]
        # Format the string
        if align == '<':
            ascii_string = ascii_string.ljust(length, fill)
        elif align == '>':
            ascii_string = ascii_string.rjust(length, fill)
        else:
            assert False, _('Wrong aling option. It should be < or >')
        # Sanity-check
        assert len(ascii_string) == length, \
            _("The formated string must match the given length")
        # Return string
        return ascii_string

    def _formatNumber(self, number, int_length, dec_length=0,
                      include_sign=False):
        """Formats the number into a fixed length ASCII (iso-8859-1) record.
        Note:
            'Todos los campos numéricos se presentarán alineados a la derecha
            y rellenos a ceros por la izquierda sin signos y sin empaquetar.'
            (http://www.boe.es/boe/dias/2008/10/23/pdfs/A42154-42190.pdf)
        """
        # Separate the number parts (-55.23 => int_part=55, dec_part=0.23,
        # sign='N')
        if number == '':
            number = 0.0
        number = float(number)
        sign = number >= 0 and ' ' or 'N'
        number = abs(number)
        int_part = int(number)
        # Format the string
        ascii_string = ''
        if include_sign:
            ascii_string += sign
        if dec_length > 0:
            ascii_string += '%0*.*f' % (int_length + dec_length + 1,
                                        dec_length, number)
            ascii_string = ascii_string.replace('.', '')
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

    def _get_formatted_declaration_record(self, cr, uid, report, context=None):
        return ''

    def _get_formatted_main_record(self, cr, uid, report, context=None):
        return ''

    def _get_formatted_other_records(self, cr, uid, report, context=None):
        return ''

    def _do_global_checks(self, report, contents, context=None):
        return True

    def action_get_file(self, cr, uid, ids, context=None):
        """Action that exports the data into a BOE formatted text file.
        @return: Action dictionary for showing exported file.
        """
        if not context.get('active_id') or not context.get('active_model'):
            return False
        report = self.pool[context['active_model']].browse(
            cr, uid, context['active_id'], context=context)
        contents = ''
        # Add header record
        contents += self._get_formatted_declaration_record(cr, uid, report,
                                                           context=context)
        # Add main record
        contents += self._get_formatted_main_record(cr, uid, report,
                                                    context=context)
        # Adds other fields
        contents += self._get_formatted_other_records(cr, uid, report,
                                                      context=context)
        # Generate the file and save as attachment
        file = base64.encodestring(contents)
        file_name = _("%s_report_%s.txt") % (
            report.number, time.strftime(_(DEFAULT_SERVER_DATE_FORMAT)))
        # Delete old files
        attachment_obj = self.pool['ir.attachment']
        attachment_ids = attachment_obj.search(
            cr, uid, [('name', '=', file_name),
                      ('res_model', '=', report._model._name)],
            context=context)
        if attachment_ids:
            attachment_obj.unlink(cr, uid, attachment_ids, context=context)
        attachment_obj.create(cr, uid, {"name": file_name,
                                        "datas": file,
                                        "datas_fname": file_name,
                                        "res_model": report._model._name,
                                        "res_id": report.id,
                                        }, context=context)
        self.write(cr, uid, ids,
                   {'state': 'get', 'data': file, 'name': file_name},
                   context=context)
        # Force view to be the parent one
        data_obj = self.pool['ir.model.data']
        result = data_obj._get_id(cr, uid, 'l10n_es_aeat',
                                  'wizard_aeat_export')
        view_id = data_obj.browse(cr, uid, result, context=context).res_id
        # TODO: Permitir si se quiere heredar la vista padre
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': [view_id],
            'res_id': ids[0],
            'target': 'new',
        }
