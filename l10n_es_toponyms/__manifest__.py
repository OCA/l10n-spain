# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2019 David Gómez <david.gomez@aselcis.com>
# Copyright 2020 Jose Luis Algara <osotranquilo@gmail.com>
# Copyright 2021 Tecnativa - João Marques
# Copyright 2013-2022 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Topónimos españoles",
    "version": "16.0.1.0.0",
    "development_status": "Mature",
    "author": "Spanish Localization Team, "
    "ZikZakMedia, "
    "Tecnativa, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localization",
    "depends": ["base_location_geonames_import"],
    "license": "AGPL-3",
    "data": ["security/ir.model.access.csv", "wizard/l10n_es_toponyms_wizard.xml"],
    "images": ["images/l10n_es_toponyms_config.png"],
    "maintainers": ["pedrobaeza"],
    "installable": True,
}
