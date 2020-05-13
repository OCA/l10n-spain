# Copyright 2017 Tecnativa - Sergio Teruel

{
    "name": "Pasarela de pago Redsys",
    "category": "Payment Acquirer",
    "summary": "Payment Acquirer: Redsys Implementation",
    "version": "13.0.1.0.0",
    "author": "Tecnativa," "Odoo Community Association (OCA)",
    "depends": ["payment", "website_sale"],
    "external_dependencies": {"python": ["Crypto.Cipher.DES3"]},
    "data": [
        "views/redsys.xml",
        "views/payment_acquirer.xml",
        "views/payment_redsys_templates.xml",
        "data/payment_redsys.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
