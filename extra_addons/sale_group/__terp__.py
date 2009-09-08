# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Pablo Rocandio. All Rights Reserved.
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
    "name" : "Sale Group",
    "version" : "1.0",
    "author" : "Pablo Rocandio",
    "category": "Generic Modules/Sales & Purchases",
    "description": """Sale Group
                      This module is usefull if you create manual pickings
                      from sale orders and manual invoices from pickings.
                      It allows to create pickings from selected lines from
                      diferent sale orders and invoices from selected lines 
                      from diferent sales orders""",
    "license" : "GPL-3",
    "depends" : ["base", "account", "stock", "sale"],
    "init_xml" : [],
    "update_xml" : [
        'sale_group_view.xml',
        'sale_group_wizard.xml',
        'sale_group_workflow.xml',
                   ],
    "active": False,
    "installable": True
}




