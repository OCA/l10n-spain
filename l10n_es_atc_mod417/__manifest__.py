# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl

{
    "name": "ATC Modelo 417",
    "version": "20.0.1.0.0",
    "author": "Tecnativa, Odoo Community Association (OCA)",
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
        "data/l10n.es.aeat.map.tax.csv",
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/l10n.es.aeat.map.tax.line.account.csv",
        "data/l10n.es.aeat.map.tax.line.csv",
        "reports/mod417_report.xml",
        "views/mod417_view.xml",
        "security/ir.access.csv",
    ],
    "maintainers": ["carlos-lopez-tecnativa", "carlosdauden"],
    "installable": True,
    "auto_install": False,
}
