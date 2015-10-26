# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com)
#                       Pedro Tarrafeta <pedro@acysos.com>
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 NaN (http://www.nan-tic.com)
#                       Albert Cervera i Areny <albert@nan-tic.com>
#    Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#        Ignacio Ibeas <ignacio@acysos.com>
#
#    Migración Odoo 8.0. Acysos S.L. (http://www.acysos.com) 2015
#    Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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

from openerp import _
from .log import Log


class PaymentConverterSpain(object):
    def digits_only(self, cc_in):
        """Discards non-numeric chars"""
        cc = ""
        for i in cc_in or '':
            try:
                int(i)
                cc += i
            except ValueError:
                pass
        return cc

    def to_ascii(self, text):
        """Converts special characters such as those with accents to their
        ASCII equivalents"""
        old_chars = ['á', 'é', 'í', 'ó', 'ú', 'à', 'è', 'ì', 'ò', 'ù', 'ä',
                     'ë', 'ï', 'ö', 'ü', 'â', 'ê', 'î', 'ô', 'û', 'Á', 'É',
                     'Í', 'Ú', 'Ó', 'À', 'È', 'Ì', 'Ò', 'Ù', 'Ä', 'Ë', 'Ï',
                     'Ö', 'Ü', 'Â', 'Ê', 'Î', 'Ô', 'Û', 'ñ', 'Ñ', 'ç', 'Ç',
                     'ª', 'º', '·', '\n']
        new_chars = ['a', 'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o', 'u', 'a',
                     'e', 'i', 'o', 'u', 'a', 'e', 'i', 'o', 'u', 'A', 'E',
                     'I', 'U', 'O', 'A', 'E', 'I', 'O', 'U', 'A', 'E', 'I',
                     'O', 'U', 'A', 'E', 'I', 'O', 'U', 'n', 'N', 'c', 'C',
                     'a', 'o', '.', ' ']
        for old, new in zip(old_chars, new_chars):
            text = text.replace(unicode(old, 'UTF-8'), new)
        return text

    def convert_text(self, text, size, justified='left'):
        if justified == 'left':
            return self.to_ascii(text)[:size].ljust(size)
        else:
            return self.to_ascii(text)[:size].rjust(size)

    def convert_float(self, number, size):
        text = str(int(round(number * 100, 0)))
        if len(text) > size:
            raise Log(_('Error:\n\nCan not convert float number %(number).2f '
                        'to fit in %(size)d characters.') % {
                'number': number,
                'size': size
            })
        return text.zfill(size)

    def convert_int(self, number, size):
        text = str(number)
        if len(text) > size:
            raise Log(_('Error:\n\nCan not convert integer number %(number)d '
                        'to fit in %(size)d characters.') % {
                'number': number,
                'size': size
            })
        return text.zfill(size)

    def convert(self, value, size, justified='left'):
        if not value:
            return self.convert_text('', size)
        elif isinstance(value, float):
            return self.convert_float(value, size)
        elif isinstance(value, int):
            return self.convert_int(value, size)
        else:
            return self.convert_text(value, size, justified)

    def convert_bank_account(self, value, partner_name):
        if not isinstance(value, basestring):
            raise Log(_('User error:\n\nThe bank account number of %s is not '
                        'defined.') % partner_name)
        ccc = self.digits_only(value)
        if len(ccc) != 20:
            raise Log(_('User error:\n\nThe bank account number of %s does not'
                        ' have 20 digits.') % partner_name)
        return ccc

    def bank_account_parts(self, value, partner_name):
        if not isinstance(value, basestring):
            raise Log(_('User error:\n\nThe bank account number of %s is not '
                        'defined.') % partner_name)
        ccc = self.digits_only(value)
        if len(ccc) != 20:
            raise Log(_('User error:\n\nThe bank account number of %s does '
                        'not have 20 digits.') % partner_name)
        return {'bank': ccc[:4],
                'office': ccc[4:8],
                'dc': ccc[8:10],
                'account': ccc[10:]}
