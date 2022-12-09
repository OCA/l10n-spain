# Copyright 2022 Tecnativa - Carlos Roca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    "name": "Impresión de pagaré de Cajamar en A4",
    "version": "15.0.1.0.0",
    "license": "AGPL-3",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "maintainers": ["CarlosRoca13"],
    "category": "Accounting",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": [
        "account_check_printing_report_base",
        "account_payment_promissory_note",
    ],
    "data": [
        "views/report_promissory_note.xml",
        "report/account_promissory_note_writing_report.xml",
    ],
    "installable": True,
}
