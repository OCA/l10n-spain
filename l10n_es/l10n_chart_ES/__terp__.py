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

* Define las plantilla de planes contables:
        * Plan General Contable Español 2008.
        * Plan General Contable Español PYMES 2008.
* Define la plantilla de los impuestos IVA soportado, IVA repercutido, recargos de equivalencia.
* Define la plantilla de códigos de impuestos.

Nota: Para la impresión de cuentas anuales (balance, perdidas y ganancias) 
se recomienda instalar el módulo l10n_ES_account_balance_report.
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
    ],
    "active": False,
    "installable": True
}
