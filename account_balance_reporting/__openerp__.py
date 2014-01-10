# -*- coding: utf-8 -*-
# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account balance reporting engine
#    Copyright (C) 2009 Pexego Sistemas Informáticos. All Rights Reserved
#    AvanzOSC, Avanzed Open Source Consulting 
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.com). All Rights Reserved
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
        "name" : "Account balance reporting engine",
        "version" : "0.3",
        "author" : "Pexego",
        "website" : "http://www.pexego.es",
        "category" : "Enterprise Specific Modules",
        "description": """
The module allows the user to create account balance reports and templates,
comparing the values of 'accounting concepts' between two fiscal years
or a set of fiscal periods.

Accounting concepts values can be calculated as the sum of some account balances,
the sum of its children, other account concepts or constant values.

Generated reports are stored as objects on the server,
so you can check them anytime later or edit them
(to add notes for example) before printing.

The module lets the user add new templates of the reports concepts,
and associate them an specific "XML report" (OpenERP RML files for example)
with the design used when printing.
So it is very easy to add predefined country-specific official reports.

The user interface has been designed to be as much user-friendly as it can be.

Note: It has been designed to meet Spanish/Spain localization needs,
but it might be used as a generic accounting report engine.
            """,
        "depends" : [
                'base',
                'account',
            ],
        "init_xml" : [
            ],
        "demo_xml" : [ ],
        "update_xml" : [
                'security/ir.model.access.csv',
                'account_balance_reporting_wizard.xml',
                'account_balance_reporting_template_view.xml',
                'account_balance_reporting_view.xml',
                'account_balance_reporting_workflow.xml',
                'account_balance_reporting_reports.xml',
            ],
        "installable": True
}
