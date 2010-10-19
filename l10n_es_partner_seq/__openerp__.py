# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
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
    "name" : "Secuencia empresa",
    "version" : "0.1",
    "author" : "Pablo Rocandio, Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Este módulo:
  * Vincula una secuencia al campo de código de empresa para generar el código de forma automática (sólo al crear nuevas empresas clientes o proveedores).
  * Añade un asistente para crear las cuentas a pagar y a cobrar de la empresa según su código (si no tuviera código se crea uno según la secuencia) cuyo prefijo será la cuenta contable padre indicada (por ejemplo, para cuentas a cobrar usaríamos 4300 para clientes o 4400 para deudores, para cuentas a pagar usaríamos 4000 para proveedores o 4100 para acreedores).

La secuencia de empresa por defecto se inicia en NP00101 (prefijo NP y relleno de 5 dígitos) y puede modificarse posteriormente en Administración/Personalización/Secuencias. Los códigos de las cuentas a pagar/cobrar se crearán usando los últimos dígitos necesarios del código de empresa para que, junto con el prefijo indicado, tengan el número total de dígitos estipulado. Si, por ejemplo, las cuentas son de 8 dígitos, el prefijo es 4300 y el código de empresa es NP00101 sólo se usaran los 4 últimos dígitos del código de empresa: 4300 + 0101 = 43000101.
    """,
    "license" : "GPL-3",
    "depends" : ["base","account","l10n_es",],
    "init_xml" : [],
    "update_xml" : [
        "partner_seq_sequence.xml",
        "partner_seq_wizard.xml"
        ],
    "active": False,
    "installable": True
}




