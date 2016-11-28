# -*- coding: utf-8 -*-
# Copyright 2004-2011 Luis Manuel Angueira Blanco (http://pexego.es)
# Copyright 2013 Ignacio Ibeas (http://acysos.com)
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2016 Angel Moya <odoo@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import re
from odoo.tools.safe_eval import safe_eval
from odoo import _, api, fields, exceptions, models, tools

EXPRESSION_PATTERN = re.compile(r'(\$\{.+?\})')


class L10nEsAeatReportExportToBoe(models.TransientModel):
    _name = "l10n.es.aeat.report.export_to_boe"
    _description = "Export Report to BOE Format"

    name = fields.Char(string="File name", readonly=True)
    data = fields.Binary(string="File", readonly=True)
    state = fields.Selection(
        selection=[
            ('open', 'open'),
            ('get', 'get'),
        ], string="State", default='open')

    def _format_string(self, text, length, fill=' ', align='<'):
        u"""Format the string into a fixed length ASCII (iso-8859-1) record.

        Note:
            'Todos los campos alfanuméricos y alfabéticos se presentarán
            alineados a la izquierda y rellenos de blancos por la derecha,
            en mayúsculas sin caracteres especiales, y sin vocales acentuadas.
            Para los caracteres específicos del idioma se utilizará la
            codificación ISO-8859-1. De esta forma la letra “Ñ” tendrá el
            valor ASCII 209 (Hex. D1) y la “Ç” (cedilla mayúscula) el valor
            ASCII 199 (Hex. C7).'
        """
        if not text:
            return fill * length
        # Replace accents and convert to upper
        from unidecode import unidecode
        text = unicode(text).upper()
        text = ''.join([unidecode(x) if x not in (u'Ñ', u'Ç') else x
                        for x in text])
        text = re.sub(
            ur"[^A-Z0-9\s\.,-_&'´\\:;/\(\)ÑÇ\"]", '', text, re.UNICODE | re.X)
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

    def _format_number(self, number, int_length, dec_length=0,
                       include_sign=False, positive_sign=' ',
                       negative_sign='N'):
        u"""Format the number into a fixed length ASCII (iso-8859-1) record.

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
        # Return the string assuring that is not unicode
        return str(ascii_string)

    def _format_boolean(self, value, yes='X', no=' '):
        u"""Format a boolean value into a fixed length ASCII (iso-8859-1) record.
        """
        res = value and yes or no
        # Return the string assuring that is not unicode
        return str(res)

    @api.multi
    def _do_global_checks(self, record, contents):
        return True

    @api.multi
    def action_get_file(self):
        """Action that exports the data into a BOE formatted text file.

        @return: Action dictionary for showing exported file.
        """
        active_id = self.env.context.get('active_id', False)
        active_model = self.env.context.get('active_model', False)
        if not active_id or not active_model:
            return False
        report = self.env[active_model].browse(active_id)
        contents = ''
        if report.export_config_id:
            contents += self.action_get_file_from_config(report)
        else:
            raise exceptions.UserError(_('No export configuration selected.'))
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
        return self._export_config(report, report.export_config_id)

    @api.multi
    def _export_config(self, obj, export_config):
        self.ensure_one()
        contents = ''
        for line in export_config.config_line_ids:
            contents += self._export_line_process(obj, line)
        return contents

    @api.multi
    def _export_line_process(self, obj, line):
        # usar esta variable para resolver las expresiones
        obj_merge = obj

        def merge_eval(exp):
            return safe_eval(exp, {
                'user': self.env.user,
                'object': obj_merge,
                # copy context to prevent side-effects of eval
                'context': self.env.context.copy(),
            })

        def merge(match):
            exp = str(match.group()[2:-1]).strip()
            result = merge_eval(exp)
            return result and tools.ustr(result) or ''

        val = ''
        if line.conditional_expression:
            if merge_eval(line.conditional_expression):
                return ''
        if line.repeat_expression:
            obj_list = merge_eval(line.repeat_expression)
        else:
            obj_list = [obj]
        for obj_merge in obj_list:
            if line.export_type == 'subconfig':
                val += self._export_config(obj_merge, line.subconfig_id)
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
            return self._format_string(val or '', line.size, align=align)
        elif line.export_type == 'boolean':
            return self._format_boolean(val, line.bool_yes, line.bool_no)
        else:  # float or integer
            decimal_size = (0 if line.export_type == 'integer' else
                            line.decimal_size)
            return self._format_number(
                float(val or 0),
                line.size - decimal_size - (line.apply_sign and 1 or 0),
                decimal_size, line.apply_sign,
                positive_sign=line.positive_sign,
                negative_sign=line.negative_sign)
