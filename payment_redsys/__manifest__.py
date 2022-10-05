# Copyright 2017 Tecnativa - Sergio Teruel

{
    'name': 'Pasarela de pago Redsys',
    'category': 'Payment Acquirer',
    'summary': 'Payment Acquirer: Redsys Implementation',
    'version': '12.0.2.0.1',
    'author': "Tecnativa,"
              "Odoo Community Association (OCA)",
    'website': 'https://github.com/OCA/l10n-spain',
    'depends': [
        'payment',
        'website_sale',
    ],
    "external_dependencies": {
        "python": [
            "Crypto.Cipher.DES3",
        ],
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
