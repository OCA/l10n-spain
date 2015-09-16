# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Alejandro Sanchez (http://www.asr-oss.com)
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the Affero GNU General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the Affero GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields


class Country(models.Model):

    _inherit = 'res.country'

    code_3166 = fields.Char('Country Code', size=3, required=True,
                            help='El código del país ISO 3166 (3 caractéres). '
                                 'Para España: "ESP".')

    def _auto_init(self, cr, context=None):
        res = super(Country, self)._auto_init(cr, context=context)
        cr.execute("select count(*) from pg_class as c inner join "
                   "pg_attribute as a on a.attrelid = c.oid where "
                   "a.attname = 'code_3166' and c.relkind = 'r' and "
                   "c.relname = 'res_country'")
        noupdate = True
        if not cr.rowcount:
            noupdate = False
        if noupdate:
            cr.execute("select code_3166 from res_country where code = 'ES'")
            code = cr.fetchone()
            if not code or not code[0]:
                noupdate = False
        if not noupdate:
            cr.execute("update ir_model_data set noupdate=false where "
                       "module = 'base' and model = 'res.country'")

        return res
