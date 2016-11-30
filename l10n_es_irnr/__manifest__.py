# -*- coding: utf-8 -*-
# License AGPL-3: Antiun Ingenieria S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

{
    'name': "Retenciones IRNR (No residentes)",
    'category': 'Localization/Account Charts',
    'version': '8.0.1.0.0',
    'depends': [
        'l10n_es',
    ],
    'external_dependencies': {},
    'data': [
        'data/tax_codes_irnr.xml',
        'data/taxes_irnr.xml',
        'data/fiscal_positions_irnr.xml',
        'data/fiscal_position_taxes_irnr.xml',
    ],
    'author': 'Antiun Ingeniería S.L., '
              'Odoo Community Association (OCA)',
    'website': 'http://www.antiun.com',
    'license': 'AGPL-3',
    'demo': [],
    'test': [],
    'installable': False,
}
