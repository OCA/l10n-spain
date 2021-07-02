# Copyright AvanzOSC - Ainara Galdona
# Copyright 2016 - Tecnativa - Antonio Espinosa
# Copyright 2016-2019 - Tecnativa - Pedro M. Baeza
# Copyright 2018 Valentin Vinagre <valentin.vinagre@qubiq.es>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 296",
    "version": "13.0.1.0.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa, AvanzOSC, Qubiq, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat", "l10n_es_aeat_mod216"],
    "data": [
        "security/ir.model.access.csv",
        "data/tax_code_map_mod296_data.xml",
        "data/aeat_export_mod296_line_data.xml",
        "data/aeat_export_mod296_data.xml",
        "views/mod296_views.xml",
        "security/ir_rule.xml",
    ],
    "installable": True,
}
