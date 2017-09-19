# -*- coding: utf-8 -*-
# Copyright 2017 Ainara Galdona - AvanzOSC
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "Account Asset Variation",
    "version": "8.0.1.0.0",
    "license": "AGPL-3",
    "author": "AvanzOSC, "
              "Odoo Community Association (OCA)",
    "website": "http://www.avanzosc.es",
    "contributors": [
        "Ainara Galdona <ainaragaldona@avanzosc.es>",
        "Ana Juaristi <anajuaristi@avanzosc.es>",
    ],
    "depends": [
        "l10n_es_account_asset",
    ],
    "category": "Accounting",
    "data": [
        "wizard/account_asset_variation_view.xml",
        "views/account_asset_view.xml",
        "views/account_asset_report.xml",
    ],
    "installable": True,
}
