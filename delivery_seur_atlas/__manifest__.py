# Copyright 2022 Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery SEUR Atlas",
    "summary": "Integrate SEUR Atlas API",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "17.0.1.0.0",
    "depends": [
        "delivery",
        "delivery_package_number",
        "delivery_price_method",
        "delivery_state",
    ],
    "data": ["views/delivery_carrier_views.xml"],
}
