# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Logista",
    "summary": (
        "Delivery Carrier implementation for Logista Parcel REST API v5: "
        "expeditions, plaza routing, 34-digit Code 128 PDF/ZPL labels and returns"
    ),
    "version": "18.0.1.0.0",
    "category": "Inventory/Delivery",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery_package_number",
        "delivery_state",
        "stock_picking_volume",
    ],
    "data": [
        "data/logista_data.xml",
        "report/logista_label_report.xml",
        "views/delivery_carrier_views.xml",
        "views/res_partner_views.xml",
        "views/stock_package_type_views.xml",
        "views/stock_picking_views.xml",
    ],
}
