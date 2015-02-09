# -*- coding: utf-8 -*-
##############################################################################
#
# OpenERP, Open Source Management Solution
# Copyright (c) 2015 Incaser (http://www.incaser.es)
# Sergio Teruel <sergio@incaser.es>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
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
__name__ = ("Limpia identificadores exernos de puntos, comas y guiones")


def clear_identifiers(cr):
    sql = """UPDATE ir.model.data
             SET name = replace(replace(replace(name,'.',''),',',''),'-','')
             WHERE (model='res.bank') AND (
                    (name ilike '.') OR
                    (name ilike ',') OR
                    (name ilike '-')) """
    cr.execute(sql)


def migrate(cr, version):
    if not version:
        return
    clear_identifiers(cr)
