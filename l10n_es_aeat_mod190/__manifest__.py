# Copyright 2018 Juan Vicente Pascual <jvpascual@puntsistemes.es>

{
    "name": "AEAT modelo 190",
    "version": "16.0.2.0.0",
    "category": "Localization/Accounting",
    "author": "Punt Sistemes SLU,"
    "Odoo Community Association (OCA),"
    "Vunkers IT Experts, SLU",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es", "l10n_es_aeat"],
    "data": [
        "data/perception_key_data.xml",
        "data/perception_subkey_data.xml",
        "data/aeat_export_mod190_partner_data.xml",
        "data/aeat_export_mod190_data.xml",
        "data/tax_code_map_mod190_data.xml",
        "views/account_fiscal_position.xml",
        "views/account_invoice_view.xml",
        "views/mod190_line_view.xml",
        "views/mod190_view.xml",
        "views/partner_view.xml",
        "views/account_move_view.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod190_security.xml",
    ],
    "installable": True,
}
