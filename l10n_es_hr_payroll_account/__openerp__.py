# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2014 Joaquin Gutierrez Pedrosa All Rights Reserved.
#    Copyright (c) 2014 Pedro Manuel Baeza Romero All Rights Reserved.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    'name': 'Spain - Payroll with Accounting',
    'category': 'Localization',
    'author': 'Joaquin Gutierrez - Pedro M. Baeza',
    'website': 'https://odoospain.odoo.com',
    'depends': ['l10n_es_hr_payroll', 'hr_payroll_account', 'l10n_es'],
    'version': '1.0',
    'description': """
Accounting Data for Spain Payroll Rules.
==========================================
    Add account support for Spain Payroll
    """,

    'auto_install': True,
    'demo': [],
    'data': ['data/l10n_es_hr_payroll_account_data.xml'],
    'installable': True
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: