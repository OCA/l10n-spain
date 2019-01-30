# -*- coding: utf-8 -*-
# Copyright 2017-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': 'AEAT modelo 390',
    'version': '10.0.2.0.0',
    'category': "Localisation/Accounting",
    'author': "Tecnativa, "
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    'license': 'AGPL-3',
    'depends': [
        'l10n_es',
        'l10n_es_aeat',
        'account_tax_balance',
    ],
    'data': [
        # 2017
        'data/aeat_export_mod390_sub01_data.xml',
        'data/aeat_export_mod390_sub02_data.xml',
        'data/aeat_export_mod390_sub03_data.xml',
        'data/aeat_export_mod390_sub04_data.xml',
        'data/aeat_export_mod390_sub05_data.xml',
        'data/aeat_export_mod390_sub06_data.xml',
        'data/aeat_export_mod390_sub07_data.xml',
        'data/aeat_export_mod390_sub08_data.xml',
        'data/aeat_export_mod390_main_data.xml',
        # 2018
        'data/aeat_export_mod390_2018_sub01_data.xml',
        'data/aeat_export_mod390_2018_sub02_data.xml',
        'data/aeat_export_mod390_2018_sub03_data.xml',
        'data/aeat_export_mod390_2018_sub04_data.xml',
        'data/aeat_export_mod390_2018_sub05_data.xml',
        'data/aeat_export_mod390_2018_sub06_data.xml',
        'data/aeat_export_mod390_2018_sub07_data.xml',
        'data/aeat_export_mod390_2018_sub08_data.xml',
        'data/aeat_export_mod390_2018_main_data.xml',
        'data/tax_code_map_mod390_data.xml',
        'views/mod390_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_es_aeat_mod390_security.xml',
    ],
    'installable': True,
}
