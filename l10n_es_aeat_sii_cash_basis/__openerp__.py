# -*- coding: utf-8 -*-
# Copyright 2017 FactorLibre - Ismael Calvo <ismael.calvo@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "SII Criterio de caja",
    "version": "8.0.1.0.0",
    "category": "Accounting & Finance",
    "website": "https://odoospain.odoo.com",
    "author": "Acysos S.L.,"
              "FactorLibre,"
              "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "l10n_es_aeat_sii",
        "account_payment_partner"
    ],
    "data": [
        "data/aeat_sii_mapping_payment_keys_data.xml",
        "security/ir.model.access.csv",
        "views/account_invoice_view.xml",
        "views/account_payment_mode_view.xml"
    ],
}
