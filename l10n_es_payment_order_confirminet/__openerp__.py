# -*- coding: utf-8 -*-
# (c) 2015 Serv. Tecnol. Avanzados - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    'name': 'Exportación de fichero bancario Confirminet',
    'version': '8.0.1.0.0',
    'author': 'Serv. Tecnol. Avanzados - Pedro M. Baeza, '
              'Odoo Community Association (OCA)',
    'contributors': [
        'Pedro M. Baeza <pedro.baeza@serviciosbaeza.com>',
    ],
    'category': 'Localisation/Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_payment_order',
    ],
    'data': [
        'data/payment_type_data.xml',
        'views/payment_mode_view.xml',
    ],
    'installable': True,
}
