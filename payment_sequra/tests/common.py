from odoo.addons.payment.tests.common import PaymentCommon


class SequraCommon(PaymentCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.sequra = cls._prepare_provider(
            "sequra",
            update_values={
                # Set values for create a new provider Redsys
                "sequra_user": "dummy",
                "sequra_pass": "dummy",
                "sequra_merchant": "dummy",
                "sequra_endpoint": "https://sandbox.sequrapi.com",
            },
        )
        # Override default values
        cls.provider = cls.sequra
        cls.currency = cls.currency_euro
        cls.country_spain = cls.env.ref("base.es")
        cls.country = cls.country_spain
        cls.company = cls.env.company
