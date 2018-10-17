# Copyright 2018 Tecnativa S.L. - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    'name': 'Factura simplificada referenciada en devoluciones',
    'summary': 'Permite referenciar el factura simplificada de origen en '
               'devoluciones de frontend y de backend',
    'version': '11.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'Tecnativa, '
              'Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'depends': [
        'l10n_es_pos',
        'pos_order_mgmt',
    ],
    'data': [
        'views/assets.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml'
    ],
    'application': False,
    'installable': True,
}
