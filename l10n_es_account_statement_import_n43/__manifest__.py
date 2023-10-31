# Copyright 2016 Comunitea - Omar Castiñeira
# Copyright 2013-2021 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Importación de extractos bancarios españoles (Norma 43)",
    "category": "Accounting & Finance",
    "version": "16.0.1.0.3",
    "license": "AGPL-3",
    "development_status": "Mature",
    "maintainers": ["pedrobaeza"],
    "author": "Spanish Localization Team,"
    "Tecnativa,"
    "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["account_statement_import_file"],
    "external_dependencies": {"python": ["chardet"]},
    "data": [
        "views/account_journal_views.xml",
        "wizards/account_statement_import_view.xml",
    ],
    "installable": True,
}
