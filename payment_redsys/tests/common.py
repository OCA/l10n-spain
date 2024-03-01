# Copyright 2022 Planesnet - Luis Planes, Laia Espinosa, Raul Solana
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.payment.tests.common import PaymentCommon


class RedsysCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.redsys = cls._prepare_provider(
            "redsys",
            update_values={
                # Set values for create a new provider Redsys
                "redsys_merchant_name": "Redsys test provider",
                "redsys_merchant_code": "069611024",
                "redsys_merchant_description": "Product description for Redsys test provider",
                "redsys_secret_key": "sq7HjrUOBfKmC576ILgskD5srU870gJ8",
                "redsys_merchant_data": "Merchant data",
            },
        )
        # Override default values
        cls.provider = cls.redsys
        cls.currency = cls.currency_euro
        cls.country_spain = cls.env.ref("base.es")
        cls.country = cls.country_spain
        cls.company = cls.env.company
