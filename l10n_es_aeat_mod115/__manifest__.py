# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2015-2020 Tecnativa - Pedro M. Baeza
# Copyright 2016 Tecnativa - Antonio Espinosa
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 115",
    "version": "14.0.1.0.1",
    "development_status": "Mature",
    "category": "Localisation/Accounting",
    "author": "AvanzOSC," "Tecnativa," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es", "l10n_es_aeat"],
    "data": [
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod115_security.xml",
        "data/aeat_export_mod115_data.xml",
        "data/tax_code_map_mod115_data.xml",
        "views/mod115_view.xml",
    ],
    "installable": True,
    "maintainers": ["pedrobaeza"],
}
