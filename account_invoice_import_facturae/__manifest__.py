# © 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    'name': 'Account Invoice Import Facturae',
    'version': '12.0.1.0.0',
    'category': 'Accounting & Finance',
    'license': 'AGPL-3',
    'summary': 'Import supplier invoices/refunds in facturae format',
    'author': 'Creu Blanca, Odoo Community Association (OCA)',
    'website': 'https://github.com/OCA/l10n-spain',
    'depends': [
        'account_invoice_import',
        'base_iso3166',
        'l10n_es_facturae'
    ],
    'data': [
    ],
    'external_dependencies': {
        'python': [
            'xmlsig',
        ]
    },
    'images': ['images/sshot-wizard1.png'],
    'installable': True,
}
