# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 FactorLibre
# Copyright 2020-22 Tecnativa
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Delivery SEUR",
    "summary": "Integrate SEUR webservice",
    "author": "Trey (www.trey.es), FactorLibre, Tecnativa, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Delivery",
    "version": "15.0.1.0.1",
    "depends": [
        "delivery",
        "delivery_package_number",
        "delivery_price_method",
        "delivery_state",
    ],
    "external_dependencies": {"python": ["zeep"]},
    "data": ["views/delivery_carrier_views.xml"],
}
