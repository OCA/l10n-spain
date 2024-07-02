{
    "name": "payment_sequra",
    "summary": "Allow payments with Sequra payment methods",
    "version": "17.0.1.0.1",
    "author": "seQura," "Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "website": "https://github.com/OCA/l10n-spain",
    "category": "Accounting/Payment Providers",
    "depends": ["payment"],
    "data": [
        "views/payment_sequra_templates.xml",
        "data/payment_method_data.xml",
        "data/payment_provider_data.xml",
        "views/payment_provider_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
}
