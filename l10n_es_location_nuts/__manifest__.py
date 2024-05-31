# Copyright 2015 Tecnativa - Antonio Espinosa
# Copyright 2015 Tecnativa - Jairo Llopis
# Copyright 2017 Tecnativa - David Vidal
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "NUTS Regions for Spain",
    "summary": "NUTS specific options for Spain",
    "version": "16.0.1.0.0",
    "category": "Localisation/Europe",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "base_location_nuts",
    ],
    "post_init_hook": "post_init_hook",
    "maintainers": ["rafaelbn", "edlopen"],
}
