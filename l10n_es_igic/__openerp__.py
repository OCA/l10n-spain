# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2004-2011 Pexego Sistemas Informáticos. All Rights Reserved
#    $Omar Castiñeira Saavedra$
#    $Susana Izquierdo$
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
        - Ejecutar el asistente de actualización del plan contable para que cargue los impuestos y cuentas nuevas, desde: Contabilidad/Configuración/Contabilidad financiera/Plantillas/Actualizar plan contable a partir de una plantilla de plan conta.
        - Por último si eres una empresa canaria, ejecuta el segundo asistente de configuración para poner como impuestos por defecto el IGIC 7% por ejemplo y quizás renombrar la posición fiscal de Régimen Nacional a Régimen Canario.""",
    "license" : "AGPL-3",
    "depends" : ["base","l10n_es","account","account_chart_update"],
    "init_xml" : ['taxes_data.xml',
                    'taxes_pymes_data.xml'],
    "demo_xml" : [],
    "update_xml" : ['install_igic_view.xml'],
    "active": False,
    "installable": True
}
