# -*- coding: utf-8 -*-
# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015 Pedro M. Baeza
# Copyright 2016 Antonio Espinosa <antonio.espinosa@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'AEAT modelo 115',
    'version': '9.0.1.0.0',
    'category': "Localisation/Accounting",
    'author': "AvanzOSC,"
              "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    'license': 'AGPL-3',
    'depends': [
        "l10n_es",
        "l10n_es_aeat",
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/aeat_export_mod115_data.xml',
        'data/tax_code_map_mod115_data.xml',
        'views/mod115_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
}
