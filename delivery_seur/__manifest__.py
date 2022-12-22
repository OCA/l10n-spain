# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery SEUR",
    "summary": "Integrate SEUR webservice",
    "author": "Trey (www.trey.es), FactorLibre, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "13.0.1.2.3",
    "depends": [
        "delivery",
        "delivery_package_number",
        "delivery_price_method",
        "delivery_state",
    ],
    "external_dependencies": {"python": ["zeep"]},
    "data": ["views/delivery_carrier_views.xml"],
}
