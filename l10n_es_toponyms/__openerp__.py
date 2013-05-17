# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com) All Rights Reserved.
#                       Pedro Manuel Baeza <pedro.baeza@serviciosbaeza.com>
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
    "version" : "1.2",
    "author" : "Localización española",
    "website" : "https://launchpad.net/openerp-spain",
    "category" : "Localisation/Spain",
    "description": """
Provincias, municipios y códigos postales del Estado español.

  * Añade las 52 provincias actuales del Estado español con posibilidad de 
escoger versión oficial, castellana o ambas
  * Proporciona un asistente para dar de alta los municipios asociados a los 
códigos postales del Estado español mediante registros city.city.

Los datos han sido obtenidos de GeoNames.

AVISO: Para aquellos que actualicen el módulo desde una versión 1.1 o anterior, 
tendrán que instalar con anterioridad manualmente el módulo city, incluido
también en la localización española.
""",
    "depends" : ["base","city"],
    "license" : "AGPL-3",
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
        "wizard/l10n_es_toponyms_wizard.xml",
    ],
    "active": False,
    "installable": True
}
