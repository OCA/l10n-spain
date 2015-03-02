# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP - Account balance reporting engine
#    Copyright (C) 2009 Pexego Sistemas Informáticos.
#    Borja López Soilán (Pexego) - borjals@pexego.es
#    AvanzOSC, Advanced Open Source Consulting
#    Copyright (C) 2011-2012 Iker Coranti (www.avanzosc.es)
#    Adaptado a la versión 7.0 por:
#        Juanjo Algaz <juanjoa@malagatic.com>   www.malagatic.com
#        Joaquín Gutierrez <joaquing.pedrosa@gmail.com>   gutierrezweb.es
#        Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>   serviciosbaeza.com
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
    "name": "Account balance reporting engine",
    "version": "0.3",
    "author": "Pexego,Odoo Community Association (OCA)",
    "website": "http://www.pexego.es",
    "category": "Accounting",
    "contributors": [
        "Juanjo Algaz <juanjoa@malagatic.com>",
        "Joaquín Gutierrez <joaquing.pedrosa@gmail.com>",
        "Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>",
        "Oihane Crucelaegui <oihanecrucelaegi@avanzosc.es>",
    ],
    "description": """
The module allows the user to create account balance reports and templates,
comparing the values of 'accounting concepts' between two fiscal years
or a set of fiscal periods.

Accounting concepts values can be calculated as the sum of some account
balances, the sum of its children, other account concepts or constant values.

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
    "depends": [
        "base",
        "account",
    ],
    "demo": [],
    "data": [
        "security/ir.model.access.csv",
        "views/account_balance_reporting_template_view.xml",
        "views/account_balance_reporting_report_view.xml",
        "views/account_balance_reporting_menu.xml",
        "views/account_balance_reporting_workflow.xml",
        "report/account_balance_reporting_reports.xml",
        "wizard/wizard_print_view.xml",
    ],
    "installable": True,
}
