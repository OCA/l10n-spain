# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011
#        Pexego Sistemas Informáticos. (http://pexego.es) All Rights Reserved
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

{
    'name' : "AEAT Base",
    'version' : "1.0",
    'author' : "Pexego",
    'license' : "AGPL-3",
    'contributors': ['Ignacio Ibeas (Acysos S.L.)'],
    'website' : "http://www.pexego.es, http://www.acysos.com",
    'category' : "Localisation/Accounting",
    'init_xml' : [
        ],
    'depends' : [
        "account",
        ],
    'update_xml' : [
        'security/aeat_security.xml',
        'security/ir.model.access.csv',
        'aeat_menuitem.xml',
        ],
    'demo_xml' : [],
    'test' : [],
    'auto_install': False,
    'installable': True,
    'application': False,
}