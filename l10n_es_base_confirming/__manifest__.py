# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Base confirming',
    'version': '11.0.1.0.0',
    'author': 'Comunitea, '
              'Odoo Community Association (OCA)',

    'license': 'AGPL-3',
    'category': 'Localisation/Accounting',
    'website': 'https://github.com/OCA/l10n-spain',
    'depends': [
        'account_payment_order',
    ],
    'data': [
        'views/account_payment_order.xml'
    ],
    'installable': True,
}
