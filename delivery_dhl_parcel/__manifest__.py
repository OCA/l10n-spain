# Copyright 2021 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Delivery DHL Parcel",
    "summary": "Delivery Carrier implementation for DHL Parcel using their API",
    "version": "14.0.1.4.0",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Studio73, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["delivery_package_number", "delivery_state"],
    "data": [
        "security/ir.model.access.csv",
        "views/delivery_carrier_view.xml",
        "views/stock_picking_views.xml",
        "wizard/dhl_parcel_end_day_wizard_views.xml",
    ],
}
