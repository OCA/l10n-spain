# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright :
#        (c) 2014 Antiun Ingenieria S.L. (Madrid, Spain, http://www.antiun.com)
#                 Endika Iglesias <endikaig@antiun.com>
#                 Antonio Espinosa <antonioea@antiun.com>
#
#    This program is free software: you can redistribute it and/or modify
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
    "name": "Point of sale simplified invoice",
    "version": "1.0",
    'author': 'Antiun Ingenieria S.L.',
    'maintainer': 'Antiun Ingenieria S.L.',
    'website': 'http://www.antiun.com',
    'license': 'AGPL-3',
    "category": "Point Of Sale",
    "description": """
Point of sale simplified invoice
=====================

This module adapts the ticket of the POS to the Spanish rule.
Add in tikect the logo of the company and user data.
    """,
    "depends": ['base', 'point_of_sale'],
    'data': [
        "views/pos_template.xml",
    ],
    "qweb": [
        'static/src/xml/pos.xml',
    ],
    "installable": True,
}
