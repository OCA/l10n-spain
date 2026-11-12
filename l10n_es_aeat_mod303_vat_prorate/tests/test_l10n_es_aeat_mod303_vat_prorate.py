# Copyright 2023 Tecnativa - Víctor Martínez
# Copyright 2023 Tecnativa - Pedro M. Baeza
# License AGPL-3 - See https://www.gnu.org/licenses/agpl-3.0


from typing import ClassVar

from odoo import Command, exceptions

from odoo.addons.l10n_es_aeat_mod303.tests.test_l10n_es_aeat_mod303 import (
    TestL10nEsAeatMod303Base,
)


class TestL10nEsAeatMod303VatProrate(TestL10nEsAeatMod303Base):
    taxes_sale: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "S_IVA21B": (1000, 210),
    }
    taxes_purchase: ClassVar[dict] = {
        # tax code: (base, tax_amount)
        "P_IVA21_BC": (500, 105),
    }

    def test_model_303_without_prorate(self):
        self._invoice_sale_create("2024-01-01")
        self._invoice_purchase_create("2024-01-01")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 105)
        self.assertEqual(self.model303.resultado_liquidacion, 105)
        self.assertEqual(self.model303.casilla_44, 0)

    def test_model_303_with_prorate(self):
        # Set vat prorate configuration for company
        # Company data are set by an administrator
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create({"date": "2024-01-01", "vat_prorate": 90}),
                ],
            }
        )
        # create invoices + model 303 for 1T
        self._invoice_sale_create("2024-01-01")
        self._invoice_purchase_create("2024-01-01")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 94.5)
        self.assertEqual(self.model303.resultado_liquidacion, 115.5)
        self.assertEqual(self.model303.casilla_44, 0)
        # create invoices + model 303 for 4T
        self._invoice_sale_create("2024-11-01")
        self._invoice_purchase_create("2024-11-01")
        with self.assertRaises(exceptions.ValidationError):
            self.model303_4t.vat_prorate_percent = 101
        self.model303_4t.vat_prorate_percent = 89
        self.model303_4t.button_calculate()
        self.assertEqual(self.model303_4t.prorate_account_id.code[:4], "6341")
        self.assertEqual(self.model303_4t.total_devengado, 210)
        self.assertEqual(self.model303_4t.total_deducir, 93.45)
        self.assertEqual(self.model303_4t.resultado_liquidacion, 116.55)
        self.assertEqual(self.model303_4t.casilla_44, -2.1)
        # Export to BOE and check the inclusion of field 44
        boe_wizard = self.env["l10n.es.aeat.report.export_to_boe"].create(
            {"name": "test_export_to_boe.txt"}
        )
        config = self.env.ref("l10n_es_aeat_mod303.aeat_mod303_2023_main_export_config")
        boe = boe_wizard._export_config(self.model303_4t, config)
        self.assertIn("N0000000000000210", str(boe))
        # Generate regularization move
        self.model303_4t.button_post()
        self.assertTrue(
            self.model303_4t.move_id.line_ids.filtered(lambda x: x.debit == 2.1)
        )

    def test_model_303_with_special_prorate_default(self):
        # Set vat prorate configuration for company
        # Company data are set by an administrator
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create(
                        {
                            "date": "2024-01-01",
                            "vat_prorate": 90,
                            "type": "special",
                            "special_vat_prorate_default": True,
                        },
                    ),
                ],
            }
        )
        # create invoices + model 303 for 1T
        self._invoice_sale_create("2024-01-01")
        self._invoice_purchase_create("2024-01-01")
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 94.5)
        self.assertEqual(self.model303.resultado_liquidacion, 115.5)
        self.assertEqual(self.model303.casilla_44, 0)
        # create invoices + model 303 for 4T
        self._invoice_sale_create("2024-11-01")
        self._invoice_purchase_create("2024-11-01")

        self.model303_4t.button_calculate()
        self.assertEqual(self.model303_4t.prorate_account_id.code[:4], "6391")
        self.assertEqual(self.model303_4t.total_devengado, 210)
        self.assertEqual(self.model303_4t.total_deducir, 115.5)
        self.assertEqual(self.model303_4t.resultado_liquidacion, 94.5)
        self.assertEqual(self.model303_4t.casilla_44, 21)

    def test_model_303_with_special_prorate_manual(self):
        # Set vat prorate configuration for company
        # Company data are set by an administrator
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create(
                        {
                            "date": "2024-01-01",
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
                            Command.link(t.id)
                            for t in self._get_taxes(["P_IVA21_BC"][0])
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
                            for t in self._get_taxes(["P_IVA21_BC"][0])
                        ],
                        "with_vat_prorate": True,
                    },
                ),
            ]
        }
        # create invoices + model 303 for 1T
        self._invoice_sale_create("2024-01-01")
        self._invoice_purchase_create("2024-01-01", p_inv_extra_data)
        self.model303.button_calculate()
        self.assertEqual(self.model303.total_devengado, 210)
        self.assertEqual(self.model303.total_deducir, 100.80)
        self.assertEqual(self.model303.resultado_liquidacion, 109.2)
        self.assertEqual(self.model303.casilla_44, 0)
        # create invoices + model 303 for 4T
        self._invoice_sale_create("2024-11-01")
        self._invoice_purchase_create("2024-11-01", p_inv_extra_data)
        with self.assertRaises(exceptions.ValidationError):
            self.model303_4t.vat_prorate_percent = 101
        self.model303_4t.vat_prorate_percent = 85
        self.model303_4t.button_calculate()
        self.assertEqual(self.model303_4t.prorate_account_id.code[:4], "6341")
        self.assertEqual(self.model303_4t.total_devengado, 210)
        self.assertEqual(self.model303_4t.total_deducir, 96.6)
        self.assertEqual(self.model303_4t.resultado_liquidacion, 113.40)
        self.assertEqual(self.model303_4t.casilla_44, -4.2)

    def test_button_compute(self):
        # Company data are set by an administrator
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create({"date": "2024-01-01", "vat_prorate": 10})
                ],
            }
        )
        self._invoice_purchase_create(
            "2024-01-01",
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Compra 100€ + IVA 21%",
                            "account_id": self.accounts["600000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "with_vat_prorate": True,
                            "tax_ids": [
                                Command.link(t.id)
                                for t in self._get_taxes("P_IVA21_BC")
                            ],
                        }
                    ),
                ]
            },
        )
        self._invoice_sale_create(
            "2024-01-01",
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Venta 200€ + IVA 21%",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": 200,
                            "quantity": 1,
                            "tax_ids": [
                                Command.link(t.id) for t in self._get_taxes("S_IVA21B")
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "name": "Venta 100€ exento",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [
                                Command.link(t.id) for t in self._get_taxes("S_IVA0")
                            ],
                        }
                    ),
                ]
            },
        )
        self.model303.button_compute()
        self.assertEqual(self.model303.vat_prorate_percent, 67)
        self.assertEqual(self.model303.casilla_44, 0)

    def test_button_compute_other_exempt(self):
        # Company data are set by an administrator
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create({"date": "2024-01-01", "vat_prorate": 10})
                ],
            }
        )
        self._invoice_purchase_create(
            "2024-01-01",
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Compra 100€ + IVA 21%",
                            "account_id": self.accounts["600000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "with_vat_prorate": True,
                            "tax_ids": [
                                Command.link(t.id)
                                for t in self._get_taxes("P_IVA21_BC")
                            ],
                        }
                    ),
                ]
            },
        )
        self._invoice_sale_create(
            "2024-01-01",
            {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": "Venta 200€ + IVA 21%",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": 200,
                            "quantity": 1,
                            "tax_ids": [
                                Command.link(t.id) for t in self._get_taxes("S_IVA21B")
                            ],
                        }
                    ),
                    Command.create(
                        {
                            "name": "Venta 100€ exento art. 22",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": 100,
                            "quantity": 1,
                            "tax_ids": [
                                Command.link(t.id)
                                for t in self._get_taxes("S_IVA0_ART22")
                            ],
                        }
                    ),
                ]
            },
        )
        self.model303.button_compute()
        self.assertEqual(self.model303.vat_prorate_percent, 67)
        self.assertEqual(self.model303.casilla_44, 0)

    def test_button_compute_all_taxed_rates(self):
        """Every sale tax that Odoo core types as subject counts as taxed, whatever
        its rate: 7.5 % and 0 % too."""
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create({"date": "2024-01-01", "vat_prorate": 10})
                ],
            }
        )
        lines = []
        for desc, price in (
            ("S_IVA21B", 100),
            ("S_IVA7-5B", 100),
            ("S_IVA0B", 100),
            ("S_IVA0", 100),
        ):
            lines.append(
                Command.create(
                    {
                        "name": f"Venta {price}€ {desc}",
                        "account_id": self.accounts["700000"].id,
                        "price_unit": price,
                        "quantity": 1,
                        "tax_ids": [Command.link(t.id) for t in self._get_taxes(desc)],
                    }
                )
            )
        self._invoice_sale_create("2024-01-01", {"invoice_line_ids": lines})
        self.model303.button_compute()
        # 300 taxed of 400
        self.assertEqual(self.model303.vat_prorate_percent, 75)

    def _set_general_prorate(self, date, percent):
        # Company data are set by an administrator
        self.company.sudo().write(
            {
                "with_vat_prorate": True,
                "vat_prorate_ids": [
                    Command.create({"date": date, "vat_prorate": percent})
                ],
            }
        )

    def _purchase_lines(self, *lines):
        return {
            "invoice_line_ids": [
                Command.create(
                    {
                        "name": f"Compra {price}€ {desc}",
                        "account_id": self.accounts["600000"].id,
                        "price_unit": price,
                        "quantity": 1,
                        "tax_ids": [Command.link(t.id) for t in self._get_taxes(desc)],
                    }
                )
                for desc, price in lines
            ]
        }

    def _box(self, report, number):
        return sum(
            report.tax_line_ids.filtered(lambda x: x.field_number == number).mapped(
                "amount"
            )
        )

    def test_model_303_prorate_deductible_boxes(self):
        """The non deductible part of the prorate is left out of the deductible
        boxes of investment goods [31] and of the REAGYP compensations [42]."""
        self._set_general_prorate("2024-01-01", 90)
        self._invoice_purchase_create(
            "2024-01-01",
            self._purchase_lines(("P_IVA21_BI", 1000), ("P_IVA12_AGR", 1000)),
        )
        self.model303.button_calculate()
        self.assertAlmostEqual(self._box(self.model303, 30), 1000)
        self.assertAlmostEqual(self._box(self.model303, 31), 189)
        self.assertAlmostEqual(self._box(self.model303, 42), 108)
        self.assertAlmostEqual(self.model303.total_deducir, 297)
