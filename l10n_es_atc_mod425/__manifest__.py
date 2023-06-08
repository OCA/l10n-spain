# Copyright 2017-2023 Tecnativa - Pedro M. Baeza
# Copyright 2014-2023 Binhex -  Nicolás Ramos (http://binhex.es)
# Basado en el modelo 390 de la AEAT
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
{
    "name": "ATC Modelo 425",
    "version": "16.0.1.0.0",
    "category": "Localisation/Accounting",
    "author": "Tecnativa,"
    "Binhex System Solutions,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "depends": ["l10n_es_atc_mod420", "l10n_es_igic", "l10n_es_atc"],
    "data": [
        "data/tax_code_map_mod425_data.xml",
        "data/l10n.es.atc.mod425.report.regime.code.csv",
        "data/l10n.es.atc.mod425.report.key.csv",
        "views/mod425_view.xml",
        "security/ir.model.access.csv",
        "security/l10n_es_atc_mod425_security.xml",
    ],
    "installable": True,
    "maintainers": ["nicolasramos"],
}
