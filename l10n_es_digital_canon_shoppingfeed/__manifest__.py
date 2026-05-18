# Copyright 2026 Tecnativa - Sergio Teruel
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Canon digital in shoppingfeed",
    "summary": "Take into account spanish digital canon in shoppingfeed catalogs",
    "version": "18.0.1.0.0",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "depends": ["l10n_es_digital_canon", "shoppingfeed_integration"],
    "data": [
        "views/shoppingfeed_store_views.xml",
    ],
    "installable": True,
    "autoinstall": True,
}
