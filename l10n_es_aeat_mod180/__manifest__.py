# -*- encoding: utf-8 -*-
# Copyright 2021-2022 Netkia
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
{
    'name': 'Modelo 180',
    'summary': 'Modelo 180',
    'description': '''
    - Modelo 180 \n''',
    'author': 'Netkia,'
              "Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'https://github.com/OCA/l10n-spain',
    'version': '12.0.1.0.0',
    'category': "Localization/Accounting",
    'depends': [
        'l10n_es_aeat_mod115',
    ],
    'data': [
        'data/aeat_export_mod180_line_data.xml',
        'data/aeat_export_mod180_data.xml',
        'security/ir.model.access.csv',
        'security/l10n_es_aeat_mod180_security.xml',
        'views/res_partner_views.xml',
        'views/informacion_catastral_views.xml',
        'views/mod180_views.xml',
        'views/account_invoice_views.xml',
        'views/account_move_views.xml',
        'views/account_move_line_views.xml',
        'views/registro_perceptor_views.xml',
    ],
    'installable': True,
}
