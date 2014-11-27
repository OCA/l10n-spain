# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) All rights reserved:
#       2013      Guadaltech (http://www.guadaltech.es)
#                 Alberto Martín Cortada
#       2014      Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                 Pedro M. Baeza <pedro.baeza@serviciobaeza.com>
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
    "name": "AEAT modelo 303",
    "version": "1.1",
    "author": "GuadalTech",
    "license": "AGPL-3",
    "website": "http://www.guadaltech.es",
    'contributors': ["Pedro M. Baeza <pedro.baeza@serviciosbaeza.com"],
    "category": "Localisation/Accounting",
    "description": """
Módulo para la presentación del modelo 303 (IVA - Autodeclaración) de la
Agencia Española de Administración Tributaria.

Instrucciones del modelo: http://goo.gl/pgVbXH

Incluye la exportación al formato BOE para su uso telemático.
        """,
    "depends": [
        "l10n_es_aeat",
    ],
    "data": [
        "wizard/export_mod303_to_boe.xml",
        "mod303_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
