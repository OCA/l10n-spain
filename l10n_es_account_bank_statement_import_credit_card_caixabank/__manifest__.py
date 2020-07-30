# Copyright 2020 ForgeFlow
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Importación de extractos bancarios tarjetas crédito CaixaBank",
    "category": "Accounting & Finance",
    "version": "13.0.1.0.1",
    "license": "AGPL-3",
    "author": "ForgeFlow," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": [
        "account_bank_statement_import",
        # https://github.com/OCA/community-data-files
        "base_currency_iso_4217",
    ],
    "data": ["wizards/account_bank_statement_import_view.xml"],
    "installable": True,
}
