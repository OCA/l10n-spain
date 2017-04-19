# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (c) 2011 Ting (http://www.ting.es) All Rights Reserved.
#    Copyright (c) 2011-2013 Acysos S.L. (http://acysos.com)
#                       Ignacio Ibeas Izquierdo <ignacio@acysos.com>
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
    'name': 'Generación de fichero modelo 340 y libro de IVA',
    'version': '8.0.2.4.0',
    "author": "Spanish Localization Team,"
              # "Acysos S.L., "
              # "Ting, "
              # "Nan-tic, "
              # "OpenMind Systems, "
              # "Serv. Tecnol. Avanzados - Pedro M. Baeza, "
              "Odoo Community Association (OCA), ",
              # "Factor Libre, "
              # "GAFIC SLP - Albert Cabedo"
    'website': 'https://github.com/OCA/l10n-spain',
    'category': 'Localisation/Accounting',
    'license': 'AGPL-3',
    'depends': [
        'account',
        'base_vat',
        'l10n_es',
        'l10n_es_aeat',
        'account_refund_original',
        'account_chart_update',
        'account_invoice_currency',
        'l10n_es_aeat_mod349'
    ],
    'data': [
        'report/report_view.xml',
        'wizard/export_mod340_to_boe.xml',
        'views/mod340_view.xml',
        'security/ir.model.access.csv',
        # 'views/res_partner_view.xml',
        'data/mod340_sequence.xml',
        'views/account_invoice_view.xml',
        'views/account_view.xml',
        'data/taxes_data.xml',
    ],
    'installable': True,
}
