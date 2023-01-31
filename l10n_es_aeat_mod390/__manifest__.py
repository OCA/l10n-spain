# Copyright 2017-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    'name': 'AEAT modelo 390',
    'version': '12.0.4.1.1',
    'category': "Localisation/Accounting",
    'author': "Tecnativa, "
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_aeat_mod303_extra_data',
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
        # 2019
        'data/aeat_export_mod390_2019_sub01_data.xml',
        'data/aeat_export_mod390_2019_sub02_data.xml',
        'data/aeat_export_mod390_2019_sub03_data.xml',
        'data/aeat_export_mod390_2019_sub04_data.xml',
        'data/aeat_export_mod390_2019_sub05_data.xml',
        'data/aeat_export_mod390_2019_sub06_data.xml',
        'data/aeat_export_mod390_2019_sub07_data.xml',
        'data/aeat_export_mod390_2019_sub08_data.xml',
        'data/aeat_export_mod390_2019_main_data.xml',
        # 2021
        'data/aeat_export_mod390_2021_sub01_data.xml',
        'data/aeat_export_mod390_2021_sub02_data.xml',
        'data/aeat_export_mod390_2021_sub03_data.xml',
        'data/aeat_export_mod390_2021_sub04_data.xml',
        'data/aeat_export_mod390_2021_sub05_data.xml',
        'data/aeat_export_mod390_2021_sub06_data.xml',
        'data/aeat_export_mod390_2021_sub07_data.xml',
        'data/aeat_export_mod390_2021_sub08_data.xml',
        'data/aeat_export_mod390_2021_main_data.xml',
        # 2022
        'data/2022/aeat.model.export.config.csv',
        'data/2022/aeat.model.export.config.line.csv',
        # rest of the stuff
        'data/tax_code_map_mod390_data.xml',
        'views/mod390_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_es_aeat_mod390_security.xml',

    ],
    'installable': True,
    'maintainers': [
        'pedrobaeza',
    ],
}
