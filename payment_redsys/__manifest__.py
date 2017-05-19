# -*- coding: utf-8 -*-

{
    'name': 'Redsys Payment Acquirer',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Redsys Implementation',
    'description': 'A payment gateway to accept online payments via credit '
                   'cards',
    'version': '10.0.1.0.0',
    'author': "Tecnativa,"
              "Odoo Community Association (OCA)",
    'depends': [
        'website_portal_sale',
    ],
    "external_dependencies": {
        "python": [
            "Crypto.Cipher.DES3",
        ],
        "bin": [],
    },
    'data': [
        'views/redsys.xml',
        'views/payment_acquirer.xml',
        'data/payment_redsys.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
}
