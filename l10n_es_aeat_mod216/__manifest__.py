# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2015-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 216",
    "version": "16.0.1.1.0",
    "category": "Localisation/Accounting",
    "author": "AvanzOSC, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat", "l10n_es_irnr"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/tax_code_map_mod216_data.xml",
        "data/aeat_export_mod216_data.xml",
        "views/mod216_view.xml",
    ],
    "maintainers": ["pedrobaeza"],
    "development_status": "Mature",
    "installable": True,
}
