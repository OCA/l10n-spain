# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c)
#        2014 - Anubía, soluciones en la nube,SL (http://www.anubia.es)
#                 Juan Formoso <jfv@anubia.es>
#                 Alejandro Santana <alejandrosantana@anubia.es>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses
#
##############################################################################

{
    "name": "Account Balance Reporting to XLS",
    "version": "1.0",
    "author": "Spanish Localization Team",
    'website': 'http://odoo-spain.org',
    "category": "Accounting / Reports",
    "description": """
Excel export for account balance reporting engine
=================================================

This module allows to export financial reports to XLS files from print dialog.

**WARNING:** This module requires module *report_xls*, available on:

  https://github.com/OCA/reporting-engine/

Contributors
------------
* Alejandro Santana <alejandrosantana@anubia.es>
* Juan Formoso <jfv@anubia.es>
* Pedro M. Baeza <pedro.baeza@serviciosbaeza.com
    """,
    'depends': [
        'account_balance_reporting',
        'report_xls',
    ],
    'contributors': [
        'Alejandro Santana <alejandrosantana@anubia.es>',
        'Juan Formoso <jfv@anubia.es>',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com',
    ],
    'external_dependencies': {
        'python': ['xlwt'],
    },
    'data': [
        'wizard/account_balance_reporting_wizard.xml',
    ],
    'installable': True,
}
