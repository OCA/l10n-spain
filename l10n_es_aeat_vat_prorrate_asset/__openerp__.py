# -*- coding: utf-8 -*-
# Copyright 2015-2017 Tecnativa - Pedro M. Baeza <pedro.baeza@tecnativa.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

{
    "name": "AEAT - Prorrata de IVA - Extensión para los activos",
    "version": "8.0.1.0.0",
    "license": "AGPL-3",
    "author": "Tecnativa, "
              "Odoo Community Association (OCA)",
    "website": "https://www.tecnativa.com",
    "category": "Accounting",
    "depends": [
        'l10n_es_aeat_vat_prorrate',
        'account_asset',
    ],
    "data": [
        'views/account_asset_asset_view.xml',
        'views/account_invoice_view.xml',
    ],
    "installable": True,
}
