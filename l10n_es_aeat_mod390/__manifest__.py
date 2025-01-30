# Copyright 2017-2023 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

{
    "name": "AEAT modelo 390",
    "version": "16.0.2.9.1",
    "category": "Localisation/Accounting",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat_mod303"],
    "data": [
        "data/aeat_export_mod390_2019_sub01_data.xml",
        "data/aeat_export_mod390_2019_sub02_data.xml",
        "data/aeat_export_mod390_2019_sub03_data.xml",
        "data/aeat_export_mod390_2019_sub04_data.xml",
        "data/aeat_export_mod390_2019_sub05_data.xml",
        "data/aeat_export_mod390_2019_sub06_data.xml",
        "data/aeat_export_mod390_2019_sub07_data.xml",
        "data/aeat_export_mod390_2019_sub08_data.xml",
        "data/aeat_export_mod390_2019_main_data.xml",
        "data/tax_code_map_mod390_data.xml",  # should be before 204 tax mapping
        # 2021
        "data/2021/aeat.model.export.config.csv",
        "data/2021/aeat.model.export.config.line.csv",
        # 2022
        "data/2022/aeat.model.export.config.csv",
        "data/2022/aeat.model.export.config.line.csv",
        # 2023
        "data/2023/aeat.model.export.config.csv",
        "data/2023/aeat.model.export.config.line.csv",
        # 2024
        "data/2024/aeat.model.export.config.csv",
        "data/2024/aeat.model.export.config.line.csv",
        "data/2024/l10n.es.aeat.map.tax.csv",
        "data/2024/l10n.es.aeat.map.tax.line.csv",
        # rest of stuff
        "views/mod390_view.xml",
        "views/account_move_view.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_aeat_mod390_security.xml",
    ],
    "installable": True,
    "maintainers": ["pedrobaeza"],
}
