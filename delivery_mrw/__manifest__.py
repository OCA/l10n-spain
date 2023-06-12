# Copyright 2022 ForgeFlow, S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery MRW",
    "summary": "Delivery Carrier implementation for MRW with SAGEC API",
    "version": "14.0.1.1.3",
    "category": "Stock",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "delivery_package_number",
        "delivery_state",
    ],
    "external_dependencies": {"python": ["zeep"]},
    "data": [
        "views/delivery_mrw_view.xml",
        "views/stock_picking_views.xml",
        "views/mrw_manifest_template.xml",
        "wizard/stock_immediate_transfer_views.xml",
        "wizard/mrw_manifest_wizard_views.xml",
        "data/delivery_mrw.xml",
        "security/ir.model.access.csv",
    ],
}
