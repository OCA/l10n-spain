# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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
    "name" : "Topónimos españoles",
    "version" : "1.0",
    "author" : "Spanish Localization Team",
    "website" : "https://launchpad.net/openerp-spain",
    "category" : "Localisation/Europe",
    "description": """
Provincias, municipios y códigos postales de España.

  * Añade las 52 provincias actuales de España con posibilidad de escoger 
    entre versión oficial, española o ambas.
  * Proporciona un asistente para dar de alta los municipios y provincias por 
    defecto asociados a los códigos postales españoles. 
  * Utilizando el módulo base_location, permite rellenar automáticamente los 
    campos ciudad y provincia del formulario de empresa, de contacto y de 
    compañía a partir del código postal o el nombre de la ciudad.

Los datos han sido obtenidos de GeoNames (http://www.geonames.org).

**AVISO:** Este módulo requiere el módulo *base_location*, disponible en:

https://launchpad.net/partner-contact-management
""",
    "depends" : ["base", "base_location"],
    "license" : "AGPL-3",
    "data" : [
        "wizard/l10n_es_toponyms_wizard.xml",
    ],
    'images': ['images/l10n_es_toponyms_config.png',],
    "demo" : [ ],
    "active": False,
    "installable": True
} 
