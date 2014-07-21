# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
#
#   This program is free software: you can redistribute it and/or modify
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
    "name" : "IGIC",
    "version" : "1.0",
    "author" : "Pexego",
    'website' : 'https://launchpad.net/openerp-spain',
    "category" : "Localisation/Account Charts",
    "description": """Añade las cuentas y impuestos del IGIC a las plantillas.
    Se usa el módulo account_chart_update para la actualización de las propias cuentas e impuestos-
    Instalación:
        - Ejecutar el primer asistente de configuración parta que actualice los impuestos y cuentas en nuetyro plan contable y nuetrs tablla de impuestos.
        - Si eres una empresa canaria, ejecuta el segundo asistente de configuración para poner como impuestos por defecto IGIC 5% y quizás renombrar la posición fiscal de Régimen Nacional a Régimen Canario.
        Sino saltad para seguir conservando por defecto el IVA 18%.""",
    "license" : "AGPL-3",
    "depends" : ["base","l10n_es","account","account_chart_update"],
    "init_xml" : ['taxes_data.xml',
                    'taxes_pymes_data.xml'],
    "demo_xml" : [],
    "update_xml" : ['install_igic_view.xml'],
    "active": False,
    "installable": False
}
