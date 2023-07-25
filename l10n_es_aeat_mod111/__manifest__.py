# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# Copyright 2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

{
    'name': 'AEAT modelo 111',
    'version': '11.0.2.1.0',
    'category': "Localisation/Accounting",
    'author': "AvanzOSC,"
              "RGB Consulting SL,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    'license': 'AGPL-3',
    'depends': [
        'l10n_es',
        'l10n_es_aeat',
    ],
    'data': [
        'data/account_tax_group_data.xml',
        'data/account_tax_data.xml',
        'data/aeat_export_mod111_data.xml',
        'data/tax_code_map_mod111_data.xml',
        'views/mod111_view.xml',
        'security/ir.model.access.csv',
        'security/l10n_es_aeat_mod111_security.xml',
    ],
    'installable': True,
}
