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
import re
from openerp.tools.safe_eval import safe_eval as eval
from openerp import tools, models, fields, api, _

EXPRESSION_PATTERN = re.compile(r'(\$\{.+?\})')


class L10nEsAeatReportExportToBoe(models.TransientModel):
    _name = "l10n.es.aeat.report.export_to_boe"
    _description = "Export Report to BOE Format"

    name = fields.Char(string='File name', readonly=True)
    data = fields.Binary(string='File', readonly=True)
    state = fields.Selection([('open', 'open'), ('get', 'get')],
                             string="State", default='open')

    def _formatString(self, text, length, fill=' ', align='<'):
        """Formats the string into a fixed length ASCII (iso-8859-1) record.

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
        from unidecode import unidecode
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
                      include_sign=False, positive_sign=' ',
                      negative_sign='N'):
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
        sign = number >= 0 and positive_sign or negative_sign
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

    @api.multi
    def _get_formatted_declaration_record(self, report):
        """
        Returns a type 1, declaration/company, formated record.
        Format of the record:
            Tipo registro 1 – Registro de declarante:
            Posiciones   Descripción
            1            Tipo de Registro
            2-4          Modelo Declaración
            5-8          Ejercicio
            9-17         NIF del declarante
            18-57        Apellidos y nombre o razón social del declarante
            58           Tipo de soporte
            59-67        Teléfono contacto
            68-107       Apellidos y nombre contacto
            108-120      Número identificativo de la declaración
            121-122      Declaración complementaria o substitutiva
            123-135      Número identificativo de la declaración anterior
        """
        text = ''
        # Tipo de Registro
        text += '1'
        # Modelo Declaración
        text += getattr(report._model, '_aeat_number')
        # Ejercicio
        text += self._formatString(
            fields.Date.from_string(report.fiscalyear_id.date_start).year, 4)
        # NIF del declarante
        text += self._formatString(report.company_vat, 9)
        # Apellidos y nombre o razón social del declarante
        text += self._formatString(report.company_id.name, 40)
        # Tipo de soporte
        text += self._formatString(report.support_type, 1)
        # Persona de contacto (Teléfono)
        text += self._formatString(report.contact_phone, 9)
        # Persona de contacto (Apellidos y nombre)
        text += self._formatString(report.contact_name, 40)
        # Número identificativo de la declaración
        text += self._formatString(report.name, 13)
        # Declaración complementaria
        text += self._formatString(report.type, 2).replace('N', ' ')
        # Número identificativo de la declaración anterior
        text += self._formatNumber(report.previous_number, 13)
        return text

    @api.multi
    def _get_formatted_main_record(self, record):
        return ''

    @api.multi
    def _get_formatted_other_records(self, record):
        return ''

    @api.multi
    def _do_global_checks(self, record, contents):
        return True

    @api.multi
    def action_get_file(self):
        """
        Action that exports the data into a BOE formatted text file.
        @return: Action dictionary for showing exported file.
        """
        active_id = self.env.context.get('active_id', False)
        active_model = self.env.context.get('active_model', False)
        if not active_id or not active_model:
            return False
        report = self.env[active_model].browse(active_id)
        contents = ''
        if report.export_config:
            contents += self.action_get_file_from_config(report)
        else:
            # Add header record
            contents += self._get_formatted_declaration_record(report)
            # Add main record
            contents += self._get_formatted_main_record(report)
            # Adds other fields
            contents += self._get_formatted_other_records(report)
            # Generate the file and save as attachment
        file = base64.encodestring(contents)
        file_name = _("%s_report_%s.txt") % (report.number,
                                             fields.Date.today())
        # Delete old files
        attachment_obj = self.env['ir.attachment']
        attachment_ids = attachment_obj.search(
            [('name', '=', file_name),
             ('res_model', '=', report._model._name)])
        attachment_ids.unlink()
        attachment_obj.create({"name": file_name,
                               "datas": file,
                               "datas_fname": file_name,
                               "res_model": report._model._name,
                               "res_id": report.id,
                               })
        self.write({'state': 'get', 'data': file, 'name': file_name})
        # Force view to be the parent one
        data_obj = self.env.ref('l10n_es_aeat.wizard_aeat_export')
        # TODO: Permitir si se quiere heredar la vista padre
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'view_mode': 'form',
            'view_type': 'form',
            'view_id': [data_obj.id],
            'res_id': self.id,
            'target': 'new',
        }

    @api.multi
    def action_get_file_from_config(self, report):
        self.ensure_one()
        return self._export_config(report, report.export_config)

    @api.multi
    def _export_config(self, obj, export_config):
        self.ensure_one()
        contents = ''
        for line in export_config.config_lines:
            contents += self._export_line_process(obj, line)
        return contents

    @api.multi
    def _export_line_process(self, obj, line):
        # usar esta variable para resolver las expresiones
        obj_merge = obj

        def merge(match):
            exp = str(match.group()[2:-1]).strip()
            result = eval(exp, {
                'user': self.env.user,
                'object': obj_merge,
                # copy context to prevent side-effects of eval
                'context': self.env.context.copy(),
            })
            return result and tools.ustr(result) or ''

        val = ''
        if line.conditional_expression:
            if (not EXPRESSION_PATTERN.sub(
                    merge, line.conditional_expression)):
                return ''
        if line.repeat_expression:
            obj_list = EXPRESSION_PATTERN.sub(merge, line.expression)
        else:
            obj_list = [obj]
        for obj_merge in obj_list:
            if line.export_type == 'subconfig':
                val += self._export_config(obj_merge, line.sub_config)
            else:
                if line.expression:
                    field_val = EXPRESSION_PATTERN.sub(merge, line.expression)
                else:
                    field_val = line.fixed_value
                val += self._export_simple_record(line, field_val)
        return val

    @api.multi
    def _export_simple_record(self, line, val):
        if line.export_type == 'string':
            align = '>' if line.alignment == 'right' else '<'
            return self._formatString(val or '', line.size, align=align)
        elif line.export_type == 'boolean':
            return self._formatBoolean(val, line.bool_yes, line.bool_no)
        else:
            decimal_size = (0 if line.export_type == 'integer' else
                            line.decimal_size)
            return self._formatNumber(
                float(val or 0),
                line.size - decimal_size - (line.apply_sign and 1 or 0),
                decimal_size, line.apply_sign,
                positive_sign=line.positive_sign,
                negative_sign=line.negative_sign)
