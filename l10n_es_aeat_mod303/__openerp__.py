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
    'category': "Localisation/Accounting",
    'author': "Spanish Localization Team,Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "wizard/export_mod303_to_boe.xml",
        "views/mod303_view.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
