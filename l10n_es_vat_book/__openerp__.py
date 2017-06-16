# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

{
    "name": "Libro de IVA",
    "version": "8.0.1.0.0",
    "author": "PRAXYA, "
              "Odoo Community Association (OCA)",
    "website": "http://www.praxya.com",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        'account',
        'base_vat',
        'l10n_es',
        'l10n_es_aeat',
        'account_refund_original',
        'account_chart_update',
        'account_invoice_currency',
    ],
    'data': [
        'data/map_taxes_vat_book.xml',
        'views/l10n_es_vat_book.xml',
        'views/l10n_es_vat_book_issued_lines.xml',
        'views/l10n_es_vat_book_received_lines.xml',
        'views/l10n_es_vat_book_received_tax_summary.xml',
        'views/l10n_es_vat_book_issued_tax_summary.xml',
        'views/l10n_es_vat_book_invoice_tax_lines.xml',
        'views/l10n_es_vat_book_rectification_issued_lines.xml',
        'views/l10n_es_vat_book_rectification_received_lines.xml',
        'views/l10n_es_vat_book_rectification_received_tax_summary.xml',
        'views/l10n_es_vat_book_rectification_issued_tax_summary.xml',
    ],
    "qweb": [
    ],
    "installable": True,
}
