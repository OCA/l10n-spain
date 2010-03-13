# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2006 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 NaN (http://www.nan-tic.com) All Rights Reserved.
#                       Albert Cervera i Areny <albert@nan-tic.com>
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

from tools.translate import _

def digits_only(cc_in):
    """Discards non-numeric chars"""

    cc = ""
    for i in cc_in:
        try:
            int(i)
            cc += i
        except ValueError:
            pass
    return cc

def to_ascii(text):
    """Converts special characters such as those with accents to their ASCII equivalents"""

    old_chars = ['áéíóúàèìòùäëïöüâêîôûÁÉÍÚÓÀÈÌÒÙÄËÏÖÜÂÊÎÔÛñÑçÇªº']
    new_chars = ['aeiouaeiouaeiouaeiouAEIOUAEIOUAEIOUAEIOUnNcCao']
    for old, new in zip(old_chars, new_chars):
        text = text.replace(unicode(old,'UTF-8'), new)
    return text


class Log(Exception):
    def __init__(self, content = '', error = False):
        self.content = content
        self.error = error
    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error
    def __call__(self):
        return self.content
    def __str__(self):
        return self.content

def convert_text(text, size):
    return to_ascii(text)[:size].ljust(size)

def convert_float(cr, number, size, context):
    text = str( int( round( number * 100, 0 ) ) )
    if len(text) > size:
        raise Log(_('Error:\n\nCan not convert float number %(number).2f to fit in %(size)d characters.') % {
            'number': number, 
            'size': size
        })
    return text.zfill(size)

def convert_int(cr, number, size, context):
    text = str( number )
    if len(text) > size:
        raise Log( _('Error:\n\nCan not convert integer number %(number)d to fit in %(size)d characters.') % {
            'number': number, 
            'size': size
        })
    return text.zfill(size)

def convert(cr, value, size, context):
    if value == False:
        return convert_text('', size)
    elif isinstance(value, float):
        return convert_float(cr, value, size, context)
    elif isinstance(value, int):
        return convert_int(cr, value, size, context)
    else:
        return convert_text(value, size)

def convert_bank_account(cr, value, partner_name, context):
    if not isinstance(value, basestring):
        raise Log( _('User error:\n\nThe bank account number of %s is not defined.') % partner_name )
    ccc = digits_only(value)
    if len(ccc) != 20:
        raise Log( _('User error:\n\nThe bank account number of %s does not have 20 digits.') % partner_name )
    return ccc

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

