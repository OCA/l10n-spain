# -*- coding: utf-8 -*-

{
    'name': 'Redsys Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Redsys Implementation',
    'version': '8.0.1.0.2',
    'author': "Incaser Informatica S.L.,Odoo Community Association (OCA)",
    'depends': ['payment'],
    "external_dependencies": {
        "python": [
            "Crypto.Cipher.DES3",
        ],
        "bin": [],
    },
    'data': [
        'views/redsys.xml',
        'views/payment_acquirer.xml'
    ],
<<<<<<< HEAD
    'installable': False,
=======
    'license': 'AGPL-3',
    'installable': True,
>>>>>>> upstream/8.0
}
