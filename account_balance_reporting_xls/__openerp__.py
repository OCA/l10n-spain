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
    "name": "Account balance reporting to XLS",
    "version": "1.0",
    "author": "Spanish Localization Team,Odoo Community Association (OCA)",
    'website': 'http://odoo-spain.org',
    "category": "Accounting / Reports",
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
