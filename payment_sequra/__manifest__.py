{
    "name": "payment_sequra",
    "summary": "Allow payments with Sequra payment methods",
    "version": "16.0.1.0.0",
    "author": "seQura," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "license": "AGPL-3",
    "category": "Accounting/Payment Providers",
    "depends": ["payment"],
    "data": [
        "views/payment_sequra_templates.xml",
        "data/payment_provider_data.xml",
        "views/payment_provider_views.xml",
    ],
    # "post_init_hook": "post_init_hook",
    # "uninstall_hook": "uninstall_hook",
}
