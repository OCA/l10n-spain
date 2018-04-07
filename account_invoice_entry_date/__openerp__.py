# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Account Invoice entry Date",
    "summary": "Generic Modules/Accounting",
    "version": "8.0.1.0.0",
    "category": "",
    "website": "https://odoo-community.org/",
    "author": "ISA srl, "
              "FactorLibre, "
              "Odoo Italian Community, "
              "Odoo Community Association (OCA)",
    "contributors": [
        "Ismael Calvo <ismael.calvo@factorlibre.com>"
    ],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {},
    "depends": [
        'account',
        'l10n_es_aeat_sii'
    ],
    "data": [
        'views/account_view.xml'
    ],
    "demo": [],
    "qweb": []
}
