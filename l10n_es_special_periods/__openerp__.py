# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2010 Domatix Technologies  S.L. (http://www.domatix.com) 
#                       info <info@domatix.com>
#                        Angel Moya <angel.moya@domatix.com>
#
#        $Id$
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
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

{
    "name": "Creación de periodos contables especiales",
    "version": "0.1",
    "author": "Domatix",
    "website" : "http://www.domatix.com",
    "license" : "GPL-3",
    "category": "Account",
    "depends": ["account"],
    "init_xml": [],
    "description": """
Este módulo añade un check en la creación de ejercicios para la creación 
de los periodos de apertura, cierre y perdidas y ganacias. 
También añade un botón en el ejercicio para crear esos periodos si no
se hace por medio del wizard.
    """,
    'update_xml': [
        'account_installer.xml',
    ],
    'installable': True,
    'active': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: