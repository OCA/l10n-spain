# Copyright 2025 Moduon Team S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl

from odoo import Command, exceptions

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 import (
    TestL10nEsAeatMod303Base,
)
from odoo.addons.l10n_es_aeat_mod390.tests.test_l10n_es_aeat_mod390 import (
    TestL10nEsAeatMod390Base,
)


class TestL10nEsAeatMod390VatProrate(
    TestL10nEsAeatMod390Base, TestL10nEsAeatMod303Base
):
    taxes_sale = {
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 210),
    }
    taxes_purchase = {
        # tax code: (base, tax_amount)
        "P_IVA21_BC": (500, 105),
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model390.year = "2025"
        cls.model390.date_start = "2025-01-01"
        cls.model390.date_end = "2025-12-31"

    def test_model_390_without_prorate(self):
        self._invoice_sale_create("2025-01-01")
        self._invoice_purchase_create("2025-01-01")
        self.model390.button_calculate()
        self.assertEqual(self.model390.casilla_522, 0)

    def test_model_390_with_prorate(self):
        # Set vat prorate configuration for company
        self.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create({"date": "2025-01-01", "vat_prorate": 90}),
                ],
            }
        )
        self._invoice_sale_create("2025-11-01")
        self._invoice_purchase_create("2025-11-01")
        with self.assertRaises(exceptions.ValidationError):
            self.model390.vat_prorate_percent = 101
        self.model390.vat_prorate_percent = 89
        self.model390.button_calculate()
        self.assertEqual(
            self.model390.casilla_522, -1.05
        )  # IVA 105; estimated prorate 10.5; final prorate 11.55; diff -1.05
        boe_wizard = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        config = self.env.ref("l10n_es_aeat_mod390.aeat_mod390_2024_main_export_config")
        boe = boe_wizard._export_config(self.model390, config)
        self.assertTrue(boe)

    def test_model_390_with_special_prorate_default(self):
        # Set vat prorate configuration for company
        self.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create(
                        {
                            "date": "2025-01-01",
                            "vat_prorate": 90,
                            "type": "special",
                            "special_vat_prorate_default": True,
                        },
                    ),
                ],
            }
        )
        self._invoice_sale_create("2025-01-01")
        self._invoice_purchase_create("2025-01-01")
        self.model390.button_calculate()
        self.assertEqual(
            self.model390.casilla_522, 10.5
        )  # default Definitive VAT prorate 100%
        self._invoice_sale_create("2025-11-01")
        self._invoice_purchase_create("2025-11-01")
        self.model390.button_calculate()
        self.assertEqual(self.model390.casilla_522, 21)  # calculate for all year

    def test_model_390_with_special_prorate_manual(self):
        # Set vat prorate configuration for company
        self.company.write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create(
                        {
                            "date": "2025-01-01",
                            "vat_prorate": 90,
                            "type": "special",
                            "special_vat_prorate_default": False,
                        },
                    ),
                ],
            }
        )
        p_inv_extra_data = {
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": "Test for tax(es) without prorate",
                        "account_id": self.accounts["600000"].id,
                        "price_unit": 300,
                        "quantity": 1,
                        "tax_ids": [
                            (4, t.id)
                            for t in self._get_taxes("P_IVA21_BC".split("//")[0])
                        ],
                        "with_vat_prorate": False,
                    },
                ),
                Command.create(
                    {
                        "name": "Test for tax(es) with prorate",
                        "account_id": self.accounts["600000"].id,
                        "price_unit": 200,
                        "quantity": 1,
                        "tax_ids": [
                            Command.link(t.id)
                            for t in self._get_taxes("P_IVA21_BC".split("//")[0])
                        ],
                        "with_vat_prorate": True,
                    },
                ),
            ]
        }
        self._invoice_sale_create("2025-11-01")
        self._invoice_purchase_create("2025-11-01", p_inv_extra_data)
        self.model390.vat_prorate_percent = 85
        self.model390.button_calculate()
        self.assertEqual(self.model390.casilla_522, -2.1)
