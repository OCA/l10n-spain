# Copyright 2016-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 123",
    "version": "13.0.1.1.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa, "
    "Spanish Localization Team, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es", "l10n_es_aeat"],
    "data": [
        "data/aeat_export_mod123_data.xml",
        "data/tax_code_map_mod123.xml",
        "views/mod123_view.xml",
        "security/ir.model.access.csv",
        "security/mod_123_security.xml",
    ],
    "installable": True,
}
