# Copyright 2021 PlanetaTIC - Marc Poch <mpoch@planetatic.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Delivery MRW',
    'summary': 'Delivery Carrier implementation for MRW API',
    'version': '12.0.1.0.0',
    'category': 'Stock',
    'author': 'PlanetaTIC'
              ' Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'license': 'AGPL-3',
    'depends': [
        'delivery_package_number',
        'delivery_state',
    ],
    'external_dependencies': {
        'python': ['suds'],
    },
    'data': [
        'views/delivery_mrw_views.xml',
        'views/stock_picking_views.xml',
    ],
    'installable': True,
    'auto_install': False
}
