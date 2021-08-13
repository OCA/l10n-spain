# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
{
    "name": "Delivery DB SCHENKER",
    "summary": "Delivery Carrier implementation for DB SCHENKER using their API",
    "version": "14.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Studio73, Odoo Community Association (OCA)",
    "license": "LGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state"],
    "external_dependencies": {"python": ["suds-py3"]},
    "data": [
        "views/delivery_carrier_view.xml",
        "views/stock_picking_views.xml",
    ],
}
