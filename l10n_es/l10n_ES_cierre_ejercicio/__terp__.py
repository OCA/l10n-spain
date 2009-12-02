# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2009 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#                       Jordi Esteve <jesteve@zikzakmedia.com>
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
    "name" : "Close Fiscal Year with Loss and Profit, Opening and Closing entries",
    "version" : "1.0",
    "author" : "Acysos, Zikzakmedia SL",
    "website" : "www.zikzakmedia.com",
    "category" : "Localisation/Europe",
    "description": """Close Fiscal Year creating Loss and Profit, Opening and Closing entries.
You can set the journal, period and description for each of these three entries.

Improved and ported to OpenERP 5.0 by Zikzakmedia. Based on the work done by Acysos for TinyERP 4.2.
    """,
    "license" : "GPL-3",
    "depends" : ["base","account","l10n_chart_ES",],
    "init_xml" : [],
    "update_xml" : [
        "cierre_ejercicio_wizard.xml"
        ],
    "active": False,
    "installable": True
}

