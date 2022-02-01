# Copyright 2017 Tecnativa - Sergio Teruel
# Copyright 2020 Tecnativa - João Marques
# Copyright 2022 Planesnet - Luis Planes, Laia Espinosa, Raul Solana

{
    "name": "Pasarela de pago Redsys",
    "category": "Payment Acquirer",
    "summary": "Payment Acquirer: Redsys Implementation",
    "version": "15.0.1.0.0",
    "author": "Tecnativa," "Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["payment", "website_sale"],
    "external_dependencies": {"python": ["pycrypto"]},
    "data": [
        "views/redsys.xml",
        "views/payment_acquirer.xml",
        "views/payment_redsys_templates.xml",
        "data/payment_redsys.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
