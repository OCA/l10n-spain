# -*- coding: utf-8 -*-
# © 2016 FactorLibre - Hugo Santos <hugo.santos@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Invoice export XLS",
    "version": "8.0.1.0.0",
    'author': 'Odoo Community Association (OCA),FactorLibre',
    'website': 'http://factorlibre.com',
    "category": "Accounting / Reports",
    'depends': [
        'account',
        'account_invoice_currency',
        'report_xls',
    ],
    'contributors': [
        'Hugo Santos <hugo.santos@factorlibre.com>'
    ],
    'external_dependencies': {
        'python': ['xlwt'],
    },
    'data': [
        'report/export_invoice_xls.xml',
        'wizard/xls_invoice_report_wizard.xml',
    ],
    'installable': True,
}
