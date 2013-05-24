# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    "name" : "Gestión de activos fijos para España",
    "version" : "1.0",
    "depends" : ["account_asset"],
    "author" : "Serv. Tecnol. Avanzados - Pedro M. Baeza",
    "description": """
Gestión de activos fijos española
=================================

Cambia la gestión estándar de activos fijos de OpenERP para acomodarla a las 
regulaciones españolas:
    
    * Cambia el método de cálculo para el prorrateo temporal.
    * Añade un nuevo método de cálculo para porcentaje fijo por periodo.
    * Añade la opción de trasladar la depreciación al final del periodo.
    """,
    "website" : "http://www.serviciosbaeza.com",
    "category" : "Accounting & Finance",
    "data" : [
        "account_asset_view.xml",
    ],
    "active": False,
    "installable": True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

