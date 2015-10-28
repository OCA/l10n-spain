# -*- coding: utf-8 -*-
# License AGPL-3: Antiun Ingenieria S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

{
    'name': "Importaciones con DUA",
    'category': 'Localization/Account Charts',
    'version': '8.0.1.0.0',
    'depends': [
        'product',
        'l10n_es',
    ],
    'external_dependencies': {},
    'data': [
        'data/taxes_dua.xml',
        'data/fiscal_positions_dua.xml',
        'data/fiscal_position_taxes_dua.xml',
        'data/products_dua.xml',
    ],
    'author': 'Antiun Ingeniería S.L., '
              'Odoo Community Association (OCA)',
    'website': 'http://www.antiun.com',
    'license': 'AGPL-3',
    'demo': [],
    'test': [],
    'installable': True,
}
