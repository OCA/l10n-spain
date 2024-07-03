# Copyright 2022 Studio73 - Ethan Hildick <ethan@studio73.es>
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0

{
    "name": "AEAT modelo 369",
    "version": "16.0.1.1.0",
    "category": "Accounting",
    "author": "Studio73, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_aeat", "l10n_eu_oss_oca"],
    "data": [
        "data/tax_code_map_mod369_data.xml",
        "data/2022/aeat.model.export.config.csv",
        "data/2022/l10n.es.aeat.map.tax.line.csv",
        "data/2022/00/aeat.model.export.config.line.csv",
        "data/2022/04/aeat.model.export.config.line.csv",
        "data/2022/05/aeat.model.export.config.line.csv",
        "data/2022/06/aeat.model.export.config.line.csv",
        "data/2022/07/aeat.model.export.config.line.csv",
        "data/2022/08/aeat.model.export.config.line.csv",
        "data/2022/09/aeat.model.export.config.line.csv",
        "data/2022/main/aeat.model.export.config.line.csv",
        "views/account_tax_view.xml",
        "views/mod369_view.xml",
        "security/l10n_es_aeat_mod369_security.xml",
        "security/ir.model.access.csv",
    ],
    "installable": True,
}
