# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2012 Factor Libre All Rights Reserved.
# $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
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
    "name": "Partner Auto fiscal position",
    "version": "0.1",
    "author": "Factor Libre SL",
    "category": "Localisation/Europe",
    "description": """Auto fiscal position depending on invoice address.""",
    "depends": ["base", "account", "base_vat_vies"],
    "license": "AGPL-3",
    "init_xml": ['security/config_fpos_security.xml'],
    "demo_xml": [],
    "update_xml": [
        'config_fiscal_position_view.xml',
        'security/ir.model.access.csv',
    ],
    "active": False,
    "installable": False
}
