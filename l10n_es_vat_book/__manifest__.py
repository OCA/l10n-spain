# -*- coding: utf-8 -*-
# See README.rst file on addon root folder for license details

{
    "name": "Libro de IVA",
    "version": "10.0.1.0.2",
    "author": "PRAXYA, "
              "Eficent, "
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": [
        'account',
        'base_vat',
        'l10n_es',
        'l10n_es_aeat',
    ],
    'data': [
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'data/map_taxes_vat_book.xml',
        'views/l10n_es_vat_book.xml',
        'views/l10n_es_vat_book_line.xml',
        'views/l10n_es_vat_book_tax_summary.xml',
        'views/l10n_es_vat_book_summary.xml',
        'report/common_templates.xml',
        'report/report_views.xml',
        'report/vat_book_invoices_issued.xml',
        'report/vat_book_invoices_received.xml',
    ],
    "installable": True,
}
