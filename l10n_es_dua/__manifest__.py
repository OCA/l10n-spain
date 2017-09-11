# -*- coding: utf-8 -*-
# Copyright 2017 Tecnativa - Antonio Espinosa
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
# See README.rst file on addon root folder for more details

{
    'name': "Importaciones con DUA",
    'category': 'Localization/Account Charts',
    'version': '10.0.1.0.0',
    'depends': [
        'product',
        'l10n_es',
    ],
    'data': [
        'data/taxes_dua.xml',
        'data/fiscal_positions_dua.xml',
        'data/fiscal_position_taxes_dua.xml',
        'data/products_dua.xml',
    ],
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'website': 'http://www.antiun.com',
    'license': 'AGPL-3',
    'installable': True,
}
