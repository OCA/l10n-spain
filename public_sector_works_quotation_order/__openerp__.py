# -*- coding: utf-8 -*-
##############################################################################
#
#    Mandate module for openERP
#    Copyright (C) 2015 Anubía, soluciones en la nube,SL (http://www.anubia.es)
#    @author: Juan Formoso <jfv@anubia.es>,
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
    'name': 'Public Sector Works Quotation Order',
    'summary': 'Spanish public sector works quotation orders',
    'version': '0.1',
    'license': 'AGPL-3',
    'author': 'Juan Formoso <jfv@anubia.es>',
    'website': 'http://www.anubia.es',
    'category': 'Sales',
    'depends': [
        'sale',
    ],
    'data': [
        'views/account_invoice_view.xml',
        'views/sale_order_view.xml',
        'views/stock_view.xml',
        'views/report_invoice.xml',
        'views/report_saleorder.xml',
    ],
    'demo': [],
    'test': [],
    'description': '''
''',
    'installable': True,
}
