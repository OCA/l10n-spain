# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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

{
    "name" : "Comunidades Autónomas de España",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Comunidades Autónomas del Estado Español

  * Añade un nuevo campo de comunidades autónomas al formulario de empresas y contactos.
  * Inserta todas las Comunidades Autónomas del Estado Español.
  * Proporciona un assistente para dar de alta las comunidades autónomas por defecto asociadas a los codigos postales. Permite rellenar automaticamente el campo comunidad autónoma del formulario de las empresas y contactos a partir del codigo postal.

Nota: No funciona con el módulo city instalado.""",
    "depends" : ["base"],
    "license" : "GPL-3",
    "init_xml" : ["l10n_es_toponyms_region_data.xml"],
    "demo_xml" : [ ],
    "update_xml" : [
        "l10n_es_toponyms_region_view.xml",
        "l10n_es_toponyms_region_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True
} 
