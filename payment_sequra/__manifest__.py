# -*- coding: utf-8 -*-
{
    'name': "payment_sequra",
    'summary': "Allow payments with Sequra payment methods",
    "version": "17.0.1.0.1",
    'description': """
Allow payments with Sequra payment methods.
    """,
    'author': "seQura",
    'website': "https://sequra.es",
    "license": "AGPL-3",
    'category': 'Accounting/Payment Providers',
    'version': '1.0',
    'depends': ['payment'],

    'data': [
        'views/payment_sequra_templates.xml',
        'data/payment_method_data.xml',
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
