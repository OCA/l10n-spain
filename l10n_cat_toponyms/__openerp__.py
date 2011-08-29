# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
    "name" : "Topònims dels Països Catalans",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Comarques dels Països Catalans (Catalunya, País Valencià i Illes Balears)

  * Afegeix un nou camp comarca al formulari d'empresa i contacte.
  * Insereix totes les comarques dels Països Catalans associades a cada província.
  * Proporciona un assistent per donar d'alta les comarques per defecte associats als codis postals dels Països Catalans. Permet omplenar automàticament el camp comarca del formulari d'empresa i contacte a partir del codi postal.

Nota: No funciona amb el mòdul city instal·lat.""",
    "license" : "Affero GPL-3",
    "depends" : ["base","l10n_es_toponyms"],
    "init_xml" : ["l10n_cat_toponyms_data.xml"],
    "demo_xml" : [ ],
    "update_xml" : [
        "l10n_cat_toponyms_view.xml",
        "l10n_cat_toponyms_wizard.xml",
        "security/ir.model.access.csv",
    ],
    "active": False,
    "installable": True
}
