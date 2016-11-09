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
    "name": "IGIC (Impuesto General Indirecto Canario)",
    "version": "8.0.0.1",
    "author": "David Diz Martínez <daviddiz@gmail.com>,"
              "Atlantux Consultores - Enrique Zanardi,",
              "Odoo Community Association (OCA)",
    "website": "https://github.com/daviddiz/igic",
    "category": "Localization/Europe",
    "depends": [
        "l10n_es",
    ],
    "license": "AGPL-3",
    "data": [
        "data/account_chart_template_igic.xml",
        "data/account_account_igic.xml",
        "data/tax_codes_igic.xml",
        "data/taxes_igic.xml",
        "data/account_chart_template_igic_post.xml",
        "data/fiscal_positions_igic.xml",
    ],
    'images': [],
    "demo": [],
    'test': [],
    'installable': True
}
