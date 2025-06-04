# Copyright 2023 Binhex - Nicolás Ramos
# Copyright 2025 Tecnativa - Carlos López
# Basado en el modelo 390 de la AEAT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
{
    "name": "ATC Modelo 425",
    "version": "17.0.1.0.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa,"
    "Binhex System Solutions,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_igic", "l10n_es_atc"],
    "data": [
        "security/ir.model.access.csv",
        "security/l10n_es_atc_mod425_security.xml",
        "data/l10n.es.aeat.map.tax.csv",
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/l10n.es.aeat.map.tax.line.account.csv",
        "data/l10n.es.aeat.map.tax.line.csv",
        "reports/mod425_report.xml",
        "views/mod425_view.xml",
    ],
    "installable": True,
    "maintainers": ["nicolasramos"],
}
