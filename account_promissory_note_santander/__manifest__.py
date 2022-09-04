# Copyright 2020 Obertix - Vicent Cubells
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Impresión de pagaré del Santander en A4",
    "version": "13.0.1.0.0",
    "license": "AGPL-3",
    "author": "Tecnativa," "Obertix," "Odoo Community Association (OCA)",
    "maintainers": ["cubells"],
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": [
        "account_check_printing_report_base",
        "account_payment_promissory_note",
    ],
    "data": [
        "data/account_promissory_note_report_data.xml",
        "views/report_promissory_note.xml",
        "report/account_promissory_note_writing_report.xml",
    ],
    "installable": True,
}
