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
  * Añade un asistente para crear las cuentas a pagar y a cobrar de la empresa según su código (si no tuviera código se crea uno según la secuencia).
La secuencia de empresa por defecto se inicia en NP00101 (prefijo NP y relleno de 5 dígitos) y puede modificarse posteriormente en Administración/Personalización/Secuencias. La longitud de los códigos de las cuentas a pagar/cobrar creadas dependerá del relleno del número de la secuencia. Si, por ejemplo, el relleno es de 5 dígitos, las cuentas creadas serán de 8 dígitos pues se añade 400 o 430 delante: 40000101, 43000101, ...
    """,
    "license" : "GPL-3",
    "depends" : ["base","account","l10n_chart_ES",],
    "init_xml" : [],
    "update_xml" : [
        "partner_seq_sequence.xml",
        "partner_seq_wizard.xml"
        ],
    "active": False,
    "installable": True
}




