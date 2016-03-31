# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (c)
#       2013      Guadaltech (http://www.guadaltech.es)
#                 Alberto Martín Cortada
#       2014-2015 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                 Pedro M. Baeza <pedro.baeza@serviciobaeza.com>
#       2015      AvanzOSC (http://www.avanzosc.es)
#                 Ainara Galdona
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
    "version": "8.0.1.5.0",
    'category': "Accounting & Finance",
    'author': "Guadaltech,"
              "AvanzOSC,"
              "Serv. Tecnol. Avanzados - Pedro M. Baeza,"
              "Antiun Ingeniería S.L.,"
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es",
        "l10n_es_aeat",
    ],
    "data": [
        "data/tax_code_map_mod303_data.xml",
        "data/aeat_export_mod303_data.xml",
        "views/mod303_view.xml",
        "security/ir.model.access.csv",
    ],
    'installable': False,
}
