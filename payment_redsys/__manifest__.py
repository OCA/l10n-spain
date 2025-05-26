# Copyright 2017 Tecnativa - Sergio Teruel
# Copyright 2020 Tecnativa - João Marques
# Copyright 2025 Acysos S.L. - Ignacio Ibeas
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Pasarela de pago Redsys",
    "category": "Payment Acquirer",
    "summary": "Payment Acquirer: Redsys Implementation",
    "version": "17.0.1.0.1",
    "author": "Tecnativa, Odoo Community Association (OCA)",
    "website": "https://github.com/OCA/l10n-spain",
    "depends": ["payment", "account_payment"],
    "external_dependencies": {"python": ["pycryptodome"]},
    "data": [
        "data/ir_config_parameter.xml",
        "views/payment_provider.xml",
        "views/payment_redsys_templates.xml",
        "views/account_payment_view.xml",
        "data/payment_redsys.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
