# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#
#    Copyright (c)
#        2015 - Factor Libre (http://factorlibre.com)
#                 Hugo Santos <hugo.santos@factorlibre.com>
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
    "name": "Invoice export XLS",
    "version": "1.0",
    "author": "Spanish Localization Team",
    'website': 'http://odoo-spain.org',
    "category": "Accounting / Reports",
    "description": """
Excel export for account invoices
=================================================

Allow export invoices to xls

**WARNING:** This module requires module *report_xls*, available on:

  https://github.com/OCA/reporting-engine/

Contributors
------------
* Hugo Santos <hugo.santos@factorlibre.com>
    """,
    'depends': [
        'account',
        'report_xls',
    ],
    'contributors': [
        'Hugo Santos <hugo.santos@factorlibre.com>'
    ],
    'external_dependencies': {
        'python': ['xlwt'],
    },
    'data': [
        'report/export_invoice_xls.xml',
        'wizard/xls_invoice_report_wizard.xml',
    ],
    'installable': True,
}
