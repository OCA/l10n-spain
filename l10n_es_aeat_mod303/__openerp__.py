# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013 Guadaltech. All Rights Reserved
#    Author: Alberto Martín Cortada
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
    "name" : "AEAT Model 303",
    "version" : "1.0",
    "author" : "GuadalTech",
    "license" : "AGPL-3",
    "website" : "http://www.guadaltech.es",
    "category" : "Localisation/Accounting",
    "description" :
     
        """
Módulo para la presentación del modelo 303. Exportación a formato AEAT.

        """,
        
    "init_xml" : [],
    "depends" : [
        "l10n_es_aeat","l10n_es_aeat_mod347"
    ],
    "update_xml" : [
            "mod303_view.xml","mod303_workflow.xml"
    ],
    "demo_xml" : [],
    "test" : [],
    "installable" : True,
    "active" : False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
