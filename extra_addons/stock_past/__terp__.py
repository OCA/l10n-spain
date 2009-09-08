# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 ACYSOS S.L. (http://acysos.com) All Rights Reserved.
#                       Pedro Tarrafeta <pedro@acysos.com>
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
    "name" : "Update to stock module to allow calculations of past stocks",
    "version" : "1.0",
    "author" : "ACYSOS SL",
    "category": "Generic Modules/Inventory Control",
    "description": """ Update to stock module. The stock calculation functions now 
        have a new date parameter that can be used to limit the stock reported. Inventories 
        now use the inventory date and update the stock at that date.
    """,
    "license" : "GPL-3",
    "website" : "http://acysos.com",
    "depends" : ["stock", "product", "base"],
    "init_xml" : [

    ],
    "demo_xml" : [
    ],
    "update_xml" : [
        "stock_wizard.xml",
        "stock_view.xml",
    ],
    "active": False,
    "installable": True
}
