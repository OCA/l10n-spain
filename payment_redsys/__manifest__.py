# Copyright 2017 Tecnativa - Sergio Teruel

{
    'name': 'Redsys Payment Acquirer',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Redsys Implementation',
    'version': '11.0.1.1.3',
    'author': "Tecnativa,"
              "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    'depends': [
        'website_payment',
        'website_sale',
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
        'views/payment_redsys_templates.xml',
        'data/payment_redsys.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
}
