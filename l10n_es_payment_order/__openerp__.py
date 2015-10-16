# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2008 Zikzakmedia S.L. (http://zikzakmedia.com)
#                       Jordi Esteve <jesteve@zikzakmedia.com>
#    Copyright (c) 2008 Acysos SL.
#                       Ignacio Ibeas <ignacio@acysos.com>
#    Copyright (c) 2008 Pablo Rocandio.
#    AvanzOSC, Advanced Open Source Consulting
#    Copyright (C) 2011-2012 Ainara Galdona (www.avanzosc.com).
#    Copyright (c) 2013 Serv. Tecnol. Avanzados (http://www.serviciosbaeza.com)
#                       Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>
#
# Refactorización. Acysos S.L. (http://www.acysos.com) 2012
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración OpenERP 7.0. Acysos S.L. (http://www.acysos.com) 2013
#   Ignacio Ibeas <ignacio@acysos.com>
#
# Migración Odoo 8.0. Acysos S.L. (http://www.acysos.com) 2015
#   Ignacio Ibeas <ignacio@acysos.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
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
    'name': 'Exportación de ficheros bancarios CSB 19, 32, 34 y 58',
    'version': '8.0.1.7.0',
    'author': 'Spanish Localization Team, '
              'Odoo Community Association (OCA)',
    'contributors': [
        'Ignacio Ibeas <ignacio@acysos.com>',
        'Jordi Esteve <jesteve@zikzakmedia.com>',
        'Pablo Rocandio',
        'Nan·tic',
        'Ainara Galdona <agaldona@avanzosc.es>',
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
        'Alexis de Lattre <alexis.delattre@akretion.com>'
    ],
    'category': 'Localisation/Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'depends': [
        'base',
        'account',
        'account_banking_payment_export'
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/payment_type_csb.xml',
        'views/payment_mode_view.xml',
        'views/account_banking_csb_view.xml',
        'wizard/export_csb_view.xml'
    ],
    'installable': True,
}
