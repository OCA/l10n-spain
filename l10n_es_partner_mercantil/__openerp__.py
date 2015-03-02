# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Spanish Localization Team. All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
    "name": "Partner Mercantil",
    "version": "1.0",
    "author": "Spanish Localization Team,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localisation/Europe",
    "description": """
    Añade los siguientes campos en la ficha de Empresa:
        * Libro
        * Registro Mercantil
        * Hoja
        * Folio
        * Seccion
        * Tomo
    """,
    "license": "AGPL-3",
    "depends": [
        "base",
    ],
    "data": [
        "views/partner_es_view.xml",
    ],
    "installable": True,
}
