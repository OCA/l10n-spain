# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0)

{
    "name": "Libro de IVA con Prorrata de IVA",
    "summary": "Libro de IVA con Prorrata de IVA para la localización española",
    "version": "16.0.1.0.0",
    "development_status": "Alpha",
    "category": "Accounting/Localizations",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Moduon, Odoo Community Association (OCA)",
    "maintainers": ["EmilioPascual", "rafaelbn"],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "auto_install": True,
    "depends": [
        "l10n_es_vat_book",
        "l10n_es_vat_prorate",
    ],
    "data": [],
}
