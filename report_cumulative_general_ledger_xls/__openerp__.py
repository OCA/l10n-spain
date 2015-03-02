# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2014 Factor Libre S.L (<http://www.factorlibre.com>).
#    Developer Rafael Valle
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
	"name" : "Report cumulative general ledger xls",
	"description": """Allows get cumulative general ledger in xls""",
	"version" : "1.0",
	"author" : "Factor Libre S.L,Odoo Community Association (OCA)",
	"category" : "Accounting",
	"module": "",
	"website": "http://www.factorlibre.com/",
	"depends" : ["account","account_financial_report","account_financial_report_web"],
	"init_xml" : [],
	"update_xml" : [
		"wizard/cumulative_general_ledger_xls_view.xml",
	],
	"demo_xml" : [],
	"active": False,
	"installable": True
}
