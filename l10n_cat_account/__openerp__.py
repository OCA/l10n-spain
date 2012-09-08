# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    $Id$
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
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name" : "Account names in Catalan",
    "version" : "1.0",
    "author" : "Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """This module translates the account name in the account templates from Spanish to Catalan (for Spanish 2008 chart of accounts, general or PYMES versions).

After installation and changing the account template names, you can create the chart of accounts with Catalan names or update your existing chart of accounts with the account_chart_update module.""",
    "depends" : ["base", "l10n_es"],
    "license" : "GPL-3",
    "init_xml" : [ ],
    "demo_xml" : [ ],
    "update_xml" : [
        "l10n_cat_account_view.xml",
    ],
    "active": False,
    "installable": True
} 
