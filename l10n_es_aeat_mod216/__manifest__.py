# Copyright 2015 AvanzOSC - Ainara Galdona
# Copyright 2016 Tecnativa - Antonio Espinosa
# Copyright 2015-2019 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 216",
    "version": "16.0.2.0.0",
    "category": "Localisation/Accounting",
    "author": "AvanzOSC, Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "data/2016/tax_code_map_mod216_data.xml",
        "data/2016/aeat_export_mod216_data.xml",
        "data/2024/l10n.es.aeat.map.tax.csv",
        "data/2024/l10n.es.aeat.map.tax.line.csv",
        "data/2024/aeat.model.export.config.csv",
        "data/2024/aeat.model.export.config.line.csv",
        "views/mod216_view.xml",
    ],
    "maintainers": ["pedrobaeza"],
    "development_status": "Mature",
    "installable": True,
}
