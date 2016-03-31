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
# Migración OpenERP 8.0. Acysos S.L. (http://www.acysos.com) 2015
#   Ignacio Ibeas <ignacio@acysos.com>
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


class Log(Exception):
    def __init__(self, content='', error=False):
        self.content = unicode(content)
        self.error = error

    def add(self, s, error=True):
        self.content = self.content + s
        if error:
            self.error = error

    def __call__(self):
        return self.content

    def __str__(self):
        return self.content
