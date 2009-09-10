# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
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
    "name" : "Spain - Chart of Accounts 2008",
    "version" : "2.0",
    "author" : "Spanish Localization Team",
    "category" : "Localisation/Account Charts",
    "description": """Plan general contable español 2008

* Define la plantilla del plan general contable 2008 (a utilizar desde el 01-01-2008)
* Define la plantilla de los impuestos IVA soportado, IVA repercutido, recargos de equivalencia
* Define la plantilla de códigos de impuestos
""",
    "license" : "GPL-3",
    "depends" : ["account", "base_vat", "base_iban"],
    "init_xml" : [
        "account_view.xml",
        "account_chart.xml",
        "taxes_data.xml",
        "fiscal_templates.xml",
        "account_chart_pymes.xml",
        "taxes_data_pymes.xml",
        "fiscal_templates_pymes.xml"
    ],
    "demo_xml" : [],
    "update_xml" : [
#        "l10n_chart_ES_wizard.xml",
#        "l10n_chart_ES_report.xml"
    ],
    "active": False,
    "installable": True
}
