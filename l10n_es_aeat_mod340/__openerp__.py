# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
#                       
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
    "name" : "Generación de fichero modelo 340",
    "version" : "1.0",
    "author" : "Francisco Pascual (Ting)",
    "category" : "Localisation/Accounting",
    "description" : """
Módulo para la presentación del modelo 340
********************* Esta versión se encuetra en desarrollo ************************
""",
    "website" : "www.ting.es",
    "license" : "GPL-3",
    "depends" : ["account",
                 "base_vat",
                 "l10n_es_aeat",
                 "report_aeroo_ooo"
                 ],
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : ["mod340_view.xml","mod340_workflow.xml","security/ir.model.access.csv", 'report/report_view.xml',],
    "installable" : True,
    "active" : False,
}
