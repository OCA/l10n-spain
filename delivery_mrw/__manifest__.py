# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery MRW",
    "summary": "Delivery Carrier implementation for MRW with SAGEC API",
    "version": "13.0.1.0.0",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "depends": ["delivery_package_number", "delivery_state"],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "data/delivery_mrw.xml",
        "wizards/stock_immediate_transfer_views.xml",
        "wizards/mrw_manifest_wizard_views.xml",
        "views/delivery_mrw_view.xml",
        "views/stock_picking_views.xml",
        "views/mrw_manifest_template.xml",
    ],
}
