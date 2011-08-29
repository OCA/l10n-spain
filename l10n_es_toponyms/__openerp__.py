# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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
    "name" : "Topónimos del Estado español",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Provincias, municipios y códigos postales del Estado Español

  * Traduce el país Spain por España
  * Añade las 52 provincias actuales del Estado Español con posibilidad de escoger versión oficial, castellana o ambas
  * Proporciona un asistente para dar de alta los municipios y provincias por defecto asociados a los 15839 códigos postales del Estado Español. Permite rellenar automáticamente los campos ciudad y provincia del formulario de empresa y contacto a partir del código postal.
  * Nuevo asistente de configuración que permite crear los valores por defecto según módulo city esté instalado (se crean entidades city.city) o no (se crean valores por defecto de los campos ciudad y provincia asociados al código postal).

Los datos han sido obtenidos de los datos públicos del Instituto Nacional de Estadística (INE).""",
    "depends" : ["base"],
    "license" : "Affero GPL-3",
    "init_xml" : ["l10n_es_toponyms_country.xml", ],
    "demo_xml" : [ ],
    "update_xml" : [
        "l10n_es_toponyms_wizard.xml",
    ],
    "active": False,
    "installable": True
} 
