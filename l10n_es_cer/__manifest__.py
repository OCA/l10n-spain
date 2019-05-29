# Copyright 2018 Creu Blanca
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'CER',
    'version': '11.0.0.0.0',
    'license': 'AGPL-3',
    'author': "SDi",
    'category': 'Generic Modules/Accounting',
    'website': "https://github.com/OCA/l10n-spain",
    'depends': ['product.template','account.tax','account.tax.python'],
    'data': [
        'data/account_tax_group.xml',
        'views/product_view.xml',
    ],
    'installable': True,
}
