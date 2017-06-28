# -*- coding: utf-8 -*-
# License AGPL-3: Antiun Ingenieria S.L. - Antonio Espinosa
# See README.rst file on addon root folder for more details

{
    'name': "Retenciones IRNR (No residentes)",
    'category': 'Localization/Account Charts',
    'depends': [
        'l10n_es',
    ],
    'data': [
        'data/tax_codes_irnr.xml',
        'data/taxes_irnr.xml',
        'data/fiscal_positions_irnr.xml',
        'data/fiscal_position_taxes_irnr.xml',
    ],
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'installable': True,
}
