# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery Transaher",
    "version": "18.0.1.0.0",
    "category": "Inventory/Delivery",
    "summary": (
        "Integrate Transaher SOAP Web Services "
        "(Expeditions, Token Auth, PDF/ZPL Labels, Tracking, Manifest & Tariffs)"
    ),
    "author": "Acysos S.L., Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "delivery_package_number",
        "delivery_state",
        "stock_picking_volume",
    ],
    "data": [
        "security/ir.model.access.csv",
        "data/transaher_data.xml",
        "report/transaher_reports.xml",
        "wizard/transaher_manifest_wizard_views.xml",
        "views/delivery_carrier_views.xml",
        "views/stock_picking_views.xml",
        "views/sale_order_views.xml",
        "views/res_partner_views.xml",
        "views/stock_package_type_views.xml",
    ],
    "installable": True,
    "application": False,
}
