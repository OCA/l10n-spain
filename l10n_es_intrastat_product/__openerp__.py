# -*- encoding: utf-8 -*-
##############################################################################
#
#    Spain Intrastat Product module for Odoo
#    Copyright (C) 2010-2015 Akretion (http://www.akretion.com)
#    Copyright (C) 2015 FactorLibre (http://www.factorlibre.com)
#    @author Alexis de Lattre <alexis.delattre@akretion.com>
#    @author Ismael Calvo <ismael.calvo@factorlibre.com>
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
    'name': 'Spain Intrastat Product',
    'version': '1.2',
    'category': 'Localisation/Report Intrastat',
    'license': 'AGPL-3',
    'summary': "Genera archivo para presentar las declaraciones Intrastat",
    'author': 'FactorLibre,Akretion,Odoo Community Association (OCA)',
    'website': 'http://www.factorlibre.com',
    'depends': [
        'intrastat_product',
        'sale_stock',
        'purchase',
    ],
    'data': [
        'security/intrastat_product_security.xml',
        'security/ir.model.access.csv',
        'data/transaction_type_data.xml',
        'data/intrastat_type_data.xml',
        'views/intrastat_product_view.xml',
        'views/intrastat_type_view.xml',
        'views/intrastat_product_reminder.xml',
        'views/company_view.xml',
        'views/partner_view.xml',
        'views/product_view.xml',
        'views/stock_view.xml',
        'views/invoice_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
}
