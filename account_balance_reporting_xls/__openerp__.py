# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c) All rights reserved:
#        (c) 2014      Anubía, soluciones en la nube,SL (http://www.anubia.es)
#                      Juan Formoso <jfv@anubia.es>
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
    "version": "0.1",
    "depends": [
        "account_balance_reporting",
        "report_xls",
    ],
    "author": "Juan Formoso <jfv@anubia.es>",
    "category": "Accounting / Reports",
    "description": """
    This module provides the opportunity of exporting financial reports to
XLS files.
    """,
    'depends': [
        'account_balance_reporting',
        'report_xls',
    ],
    'demo_xml': [],
    'init_xml': [],
    'update_xml': [
        'wizard/account_balance_reporting_wizard.xml',
    ],
    'installable': True,
    # 'certificate': 'certificate',
}
