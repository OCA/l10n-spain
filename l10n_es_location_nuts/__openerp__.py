# -*- coding: utf-8 -*-
# © 2015 Antiun Ingenieria S.L. - Antonio Espinosa
# © 2015 Antiun Ingenieria S.L. - Jairo Llopis
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'NUTS Regions for Spain',
    'summary': 'NUTS specific options for Spain',
    'version': '8.0.1.0.0',
    'category': 'Localisation/Europe',
    'website': 'http://www.antiun.com',
    'author': 'Antiun Ingeniería S.L., '
              'Odoo Community Association (OCA)',
    'license': 'AGPL-3',
    'application': False,
    'installable': True,
    'depends': [
        'base_location_nuts',
        'l10n_es_toponyms',
    ],
    'post_init_hook': 'post_init_hook',
}
