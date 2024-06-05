# Copyright 2016-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT modelo 123",
    "version": "17.0.1.1.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa, "
    "Spanish Localization Team, "
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es", "l10n_es_aeat"],
    "data": [
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/2024/aeat.model.export.config.csv",
        "data/2024/aeat.model.export.config.line.csv",
        "data/2024/l10n.es.aeat.map.tax.csv",
        "data/2024/l10n.es.aeat.map.tax.line.csv",
        "data/2016/aeat.model.export.config.csv",
        "data/2016/aeat.model.export.config.line.csv",
        "data/2016/l10n.es.aeat.map.tax.csv",
        "data/2016/l10n.es.aeat.map.tax.line.csv",
        "views/mod123_view.xml",
        "security/ir.model.access.csv",
        "security/mod_123_security.xml",
    ],
    "installable": True,
}
