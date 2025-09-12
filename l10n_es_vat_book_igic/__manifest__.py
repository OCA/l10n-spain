# Copyright 2014-2023 Binhex - Nicolás Ramos (http://binhex.es)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Libro de IGIC",
    "version": "17.0.1.0.0",
    "author": "Binhex System Solutions, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["l10n_es_igic", "l10n_es_vat_book"],
    "data": [
        "data/l10n.es.aeat.map.tax.line.account.csv",
        "data/l10n.es.aeat.map.tax.line.tax.csv",
        "data/aeat.vat.book.map.line.csv",
    ],
    "maintainers": ["nicolasramos"],
    "installable": True,
}
