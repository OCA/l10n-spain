# Copyright 2017 Tecnativa - Sergio Teruel
# Copyright 2020 Tecnativa - João Marques

{
    "name": "Pasarela de pago Redsys",
    "category": "Payment Acquirer",
    "summary": "Payment Acquirer: Redsys Implementation",
    "version": "15.0.1.0.1",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["payment"],
    "external_dependencies": {"python": ["pycryptodome"]},
    "data": [
        "views/payment_acquirer.xml",
        "views/payment_redsys_templates.xml",
        "data/payment_redsys.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
