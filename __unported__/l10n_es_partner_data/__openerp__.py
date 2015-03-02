# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2009 Pablo Rocandio. All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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

{
    "name" : "Datos iniciales para módulo base",
    "version" : "1.0",
    "author" : "Pablo Rocandio, Zikzakmedia SL,Odoo Community Association (OCA)",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Añade datos iniciales a las tablas:
    * Canales
    * Categorías de empresas""",
    "license" : "AGPL-3",
    "depends" : [
        "base",
        "crm",
        ],
    "init_xml" : [
        "data/data_partner_events.xml",     # Canales de comunicación
        "data/data_partner_categories.xml", # Categorías de empresas
        ],
    "demo_xml" : [],
    "update_xml" :[],
    "active": False,
    "installable": False
}


