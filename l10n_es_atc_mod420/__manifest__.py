# Copyright 2014-2022 Nicolás Ramos (http://binhex.cloud)
# Copyright 2023-2024 Christian Ramos (http://binhex.cloud)
# Copyright 2023 Binhex System Solutions

{
    "name": "ATC Modelo 420",
    "version": "18.0.1.0.0",
    "author": "Binhex, Odoo Community Association (OCA)",
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": [
        "base_location",
        "l10n_es_aeat",
        "l10n_es_atc",
        "report_xml",
    ],
    "external_dependencies": {
        "deb": ["openjdk-8-jdk", "ttf-mscorefonts-installer", "fontconfig"],
    },
    "data": [
        "security/l10n_es_atc_mod420_security.xml",
        "security/ir.model.access.csv",
        "data/l10n.es.aeat.map.tax.csv",
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/l10n.es.aeat.map.tax.line.account.csv",
        "data/l10n.es.aeat.map.tax.line.csv",
        "reports/mod420_report.xml",
        "views/mod420_view.xml",
    ],
    "maintainers": ["Christian-RB"],
    "installable": True,
    "auto_install": False,
}
