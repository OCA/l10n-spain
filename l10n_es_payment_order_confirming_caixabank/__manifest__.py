# -*- coding: utf-8 -*-
# (c) 2018 Comunitea Servicios Tecnológicos - Javier Colmenero
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
{
    'name': 'Exportación de fichero bancario Confirming para Caixabank',
    'version': '11.0.1.0.0',
    'author': 'Comunitea, '
              'Odoo Community Association (OCA)',
    'contributors': [
        'Javier Colmenero <javier@comunitea.com>',
    ],
    'category': 'Localisation/Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'depends': [
        'account_payment_order',
        'l10n_es_base_confirming'
        'partner_fax'
    ],
    'data': [
        'data/account_payment_method.xml',
        'views/account_payment_mode.xml',
    ],
    'installable': True,
}
