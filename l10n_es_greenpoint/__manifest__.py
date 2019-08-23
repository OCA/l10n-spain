# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Punto Verde',
    'version': '11.0.0.0.0',
    'license': 'AGPL-3',
    'author': "SDi, Odoo Community Association (OCA)",
    'category': 'Generic Modules/Accounting',
    'website': "https://github.com/OCA/l10n-spain",
    'depends': [
        'l10n_es',
        'product',
        'sale',
        'account_tax_python',
        ],
    'data': [
        'data/account_tax_data.xml',
        'views/product_view.xml',
        'views/account_tax_views.xml',
    ],
    'installable': True,
}
