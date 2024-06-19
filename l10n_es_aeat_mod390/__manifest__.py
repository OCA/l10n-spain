# Copyright 2017-2024 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    "name": "AEAT modelo 390",
    "version": "17.0.1.2.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat_mod303"],
    "data": [
        "data/aeat_export_mod390_2019_sub04_data.xml",
        "data/aeat_export_mod390_2019_sub07_data.xml",
        "data/aeat_export_mod390_2019_sub08_data.xml",
        # 2021
        "data/2021/aeat.model.export.config.csv",
        "data/2021/aeat.model.export.config.line.csv",
        # 2022
        "data/2022/aeat.model.export.config.csv",
        "data/2022/aeat.model.export.config.line.csv",
        # 2023
        "data/2023/aeat.model.export.config.csv",
        "data/2023/aeat.model.export.config.line.csv",
        # rest of stuff
        "data/l10n.es.aeat.map.tax.csv",
        "data/l10n.es.aeat.map.tax.line.account.csv",  # Should be before the main one
        "data/l10n.es.aeat.map.tax.line.tax.csv",  # Should be before the main one
        "data/l10n.es.aeat.map.tax.line.csv",
        "views/mod390_view.xml",
        "views/account_move_view.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod390_security.xml",
    ],
    "installable": True,
    "maintainers": ["pedrobaeza"],
}
