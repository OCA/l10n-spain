# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) 2014      Anubía, soluciones en la nube,SL (http://www.anubia.es)
#                      Juan Formoso <jfv@anubia.es>
#                      Alejandro Santana <alejandrosantana@anubia.es>
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
    "version": "0.2",
    "author": "Juan Formoso <jfv@anubia.es>",
    "category": "Accounting / Reports",
    "description": """
This module provides the opportunity of exporting financial reports to
XLS files.

This module depends on two community-effort modules, both under the
umbrella of OCA (Odoo Community Association):
- **account_balance_reporting**:
  https://github.com/OCA/l10n-spain/tree/6.1
- **report_xls**:
  https://github.com/OCA/reporting-engine/tree/6.1

To easily download it, you can use git in commandline, like this:
git clone -b 6.1 https://github.com/OCA/reporting-engine
""",
    'depends': [
        'account_balance_reporting',
        'report_xls',
    ],
    'contributors': ['Alejandro Santana <alejandrosantana@anubia.es>', ],
    'data': [
        'wizard/account_balance_reporting_wizard.xml',
    ],
    'demo': [],
    'installable': True,
    # 'certificate': 'certificate',
}
