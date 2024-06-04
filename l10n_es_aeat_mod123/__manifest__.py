# Copyright 2016-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 123",
    "version": "16.0.2.2.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa, "
    "Spanish Localization Team, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es", "l10n_es_aeat"],
    "data": [
        "data/2016/aeat_export_mod123_data.xml",
        "data/2016/tax_code_map_mod123.xml",
        "data/2024/aeat_export_mod123_data.xml",
        "data/2024/tax_code_map_mod123.xml",
        "views/mod123_view.xml",
        "security/ir.model.access.csv",
        "security/mod_123_security.xml",
    ],
    "installable": True,
}
