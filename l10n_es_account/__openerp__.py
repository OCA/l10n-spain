# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008-2010 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                            Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2013
#        Joan M. Grande <totaler@gmail.com> All Rights Reserved
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
    "name" : "Spanish account tools",
    "version" : "3.0",
    "author" : "Spanish Localization Team",
    'website' : 'https://launchpad.net/openerp-spain',
    "category" : "Localisation/Accounting",
    "description": """Adds several tools to help Spanish accountants:
  * Searching of accounts using a dot to fill the zeroes (like 43.27 to search account 43000027).
  * The account chart template field is added to account templates, tax templates, tax codes templates and fiscal positions templates in list and search views. It helps to filter the template items by the account chart template that they belong.
""",
    "license" : "AGPL-3",
    "depends" : ["l10n_es"],
    "data" : [
        "account_view.xml",
    ],
    "active": False,
    "installable": True
}
