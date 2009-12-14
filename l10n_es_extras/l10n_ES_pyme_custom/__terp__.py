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
    "name" : "Instal·lación PYME estándar (2o paso)",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "category" : "Generic Modules/Others",
    "website": "www.zikzakmedia.com",
    "description": """Instal·lación OpenERP para una PYME estándar (2o paso).

Instala los módulos de importación de extractos bancarios y datos de bancos españoles y su validación.

Previamente debe instalar el módulo l10_ES_pyme_install y crear los topónimos del Estado Español (crear las provincias mediante el asistente que se ejecuta automáticamente) y las cuentas contables a partir de la plantilla (mediante el menú Gestión financiera/Configuración/Contabilidad financiera/Plantillas/Generar plan contable a partir de una plantilla de plan contable.)""",
    "license" : "GPL-3",
    "depends" : ["l10n_ES_pyme_install", "l10n_ES_partner", "l10n_ES_extractos_bancarios"],
    "init_xml" : ["pyme_data.xml"],
    "demo_xml" : [],
    "update_xml" : [
    ],
    "active": False,
    "installable": True
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: