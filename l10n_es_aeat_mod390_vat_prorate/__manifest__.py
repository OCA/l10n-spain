# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    "name": "AEAT modelo 390 Prorate",
    "version": "18.0.1.0.0",
    "category": "Localisation/Accounting",
    "author": "Moduon, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "l10n_es_aeat_mod390",
        "l10n_es_vat_prorate",
    ],
    "data": [
        "views/mod390_views.xml",
        "data/aeat.model.export.config.line.csv",
        "data/l10n.es.aeat.map.tax.line.csv",
    ],
    "autoinstall": True,
    "maintainers": ["rafaelbn", "Andrii9090", "EmilioPascual"],
}
