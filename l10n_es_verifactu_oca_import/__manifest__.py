# Copyright 2026 Odoo Community Association (OCA)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "VERI*FACTU - External SIF invoices",
    "version": "16.0.1.0.0",
    "category": "Accounting/Localizations/EDI",
    "website": "https://github.com/OCA/l10n-spain",
    "author": "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": ["l10n_es_verifactu_oca"],
    "data": ["views/account_journal_view.xml", "views/account_move_view.xml"],
}
