# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Joaquin Gutierrez Pedrosa All Rights Reserved.
#    Copyright (c) 2014 Pedro Manuel Baeza Romero All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
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
    'name': 'Spain - Payroll',
    'version': '1.0',
    'category': 'Localization',
    'sequence': 35,
    'summary': 'Hr Payroll adapts to Spain',
    'description': """
Management PaySlip for Spain
==================================
* Add payslip categories.
* Add payslip rules.
* Add the necessary fields in contract.

    """,
    'author': 'Joaquin Gutierrez - Pedro M. Baeza',
    'website': 'https://odoospain.odoo.com/',
    'depends': ['hr_payroll'],
    'data': ['view/hr_payroll_view.xml',
             'data/hr_payroll_data.xml'],
    'installable': True,
    'auto_install': False,
    'application': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
