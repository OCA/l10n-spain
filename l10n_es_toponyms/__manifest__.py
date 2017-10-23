# -*- coding: utf-8 -*-
# Copyright 2009 Jordi Esteve <jesteve@zikzakmedia.com>
# Copyright 2013-2017 Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Topónimos españoles",
    "version": "11.0.1.0.0",
    "author": "Spanish Localization Team, "
              "ZikZakMedia, "
              "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Localization",
    "depends": [
        "base_location_geonames_import",
    ],
    "license": "AGPL-3",
    "data": [
        "wizard/l10n_es_toponyms_wizard.xml",
    ],
    'images': [
        'images/l10n_es_toponyms_config.png'
    ],
    'installable': True,
}
