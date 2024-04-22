# -*- coding: utf-8 -*-
# Copyright 2024 Binovo IT Human Project SL
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Spain - Verifactu",
    "summary": "Spain - Verifactu",
    "version": "16.0.1.0.0",
    "depends": ["l10n_es_edi_sii"],
    "data": [
        "data/account_edi_data.xml",
        "data/ir_config_parameter_data.xml",
        "views/account_verifactu_views.xml",
        "views/report_invoice.xml",
        "views/res_config_settings_views.xml",
    ],
    "demo": ["demo/demo.xml"],
    "author": "Binovo,"
              "Odoo Community Association (OCA)",
    "maintainers": ["Binovo"],
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting/Localizations/EDI",
    "application": False,
    "auto_install": False,
    "installable": True,
}
