# Copyright 2022 Sygel - Manuel Regidor
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 390 - OSS",
    "version": "17.0.1.0.0",
    "category": "Accounting",
    "author": "Sygel, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat_mod390", "l10n_eu_oss_oca"],
    "data": [
        "data/2024/l10n.es.aeat.map.tax.line.csv",
        "data/l10n.es.aeat.map.tax.line.csv",
        "data/aeat_export_mod390_sub06_data.xml",
    ],
    "installable": True,
    "autoinstall": True,
}
