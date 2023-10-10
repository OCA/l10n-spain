# Copyright 2023 Dixmit
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "AEAT Modelo 322",
    "summary": """
        AEAT modelo 322""",
    "version": "14.0.1.0.0",
    "license": "AGPL-3",
    "author": "Dixmit,Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["l10n_es_aeat_mod303"],
    "data": [
        "security/ir.model.access.csv",
        "security/security.xml",
        "views/l10n_es_aeat_mod322_group.xml",
        "views/l10n_es_aeat_mod322_report.xml",
        "data/2023/l10n.es.aeat.map.tax.csv",
        "data/2023/l10n.es.aeat.map.tax.line.csv",
        "data/2023/aeat.model.export.config.csv",
        "data/2023/aeat.model.export.config.line.csv",
    ],
    "demo": [],
}
