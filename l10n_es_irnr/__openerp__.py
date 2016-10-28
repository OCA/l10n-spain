# -*- coding: utf-8 -*-
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Retenciones IRNR (No residentes)",
    "summary": "Module summary",
    'version': '9.0.1.0.0',
    'category': 'Localization/Account Charts',
    'website': 'https://odoo-community.org',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es',
    ],
    'data': [
        'data/taxes_irnr.xml',
        'data/fiscal_positions_irnr.xml',
        'data/fiscal_position_taxes_irnr.xml',
    ],
    'installable': True,
}
