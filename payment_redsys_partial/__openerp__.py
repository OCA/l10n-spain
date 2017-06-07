# -*- coding: utf-8 -*-
# © 2016 Sergio Teruel <sergio.teruel@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Redsys Payment Partial Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Redsys Implementation with partial payment',
    'version': '8.0.1.0.1',
    'author': "Tecnativa, "
              "Odoo Community Association (OCA)",
    'depends': ['payment_redsys'],
    "external_dependencies": {
        "python": [
            "Crypto.Cipher.DES3",
        ],
        "bin": [],
    },
    'data': [
        'views/payment_acquirer.xml'
    ],
    'license': 'AGPL-3',
    'installable': True,
}
