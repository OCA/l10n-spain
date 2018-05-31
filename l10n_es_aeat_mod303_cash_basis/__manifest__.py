# -*- coding: utf-8 -*-
# Copyright 2018 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 303 - Extensión para criterio de caja",
    "version": "10.0.2.0.0",
    'category': "Accounting & Finance",
    'author': "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "account_tax_cash_basis",
        "l10n_es_aeat_mod303",
    ],
    "data": [
        "data/aeat_export_mod303_2018_data.xml",
        "data/tax_code_map_mod303_data.xml",
        "views/mod303_view.xml",
    ],
    'installable': True,
}
