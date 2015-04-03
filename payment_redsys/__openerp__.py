# -*- coding: utf-8 -*-

{
    'name': 'Redsys Payment Acquirer',
    'category': 'Hidden',
    'summary': 'Payment Acquirer: Redsys Implementation',
    'version': '8.0.1.0.0',
    'author': "Incaser Informatica S.L.,Odoo Community Association (OCA)",
    'depends': ['payment'],
    'data': [
        'views/redsys.xml',
        'views/payment_acquirer.xml'
    ],
    'installable': True,
}
