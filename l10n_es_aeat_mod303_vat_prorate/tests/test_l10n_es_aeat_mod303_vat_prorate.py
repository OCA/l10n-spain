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
        # [45] = [29] + [44]: 94.5 - 2.1 (1 % of 105 in 1T and in 4T)
        self.assertEqual(self.model303_4t.total_deducir, 92.4)
        self.assertEqual(self.model303_4t.resultado_liquidacion, 117.6)
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

    def test_model_303_with_special_prorate_refund(self):
        """A refunded bill takes its prorate out of the regularization."""
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
        self._invoice_sale_create("2024-01-01")
        bill = self._invoice_purchase_create("2024-01-01")
        self._invoice_refund(bill, "2024-02-01")
        self._invoice_sale_create("2024-11-01")
        self._invoice_purchase_create("2024-11-01")
        self.model303_4t.button_calculate()
        # Prorate lines of the year: 10.5 - 10.5 + 10.5; definitive 100 %:
        # 10.5 x 10 / 10
        self.assertEqual(self.model303_4t.casilla_44, 10.5)
        self.assertEqual(self.model303_4t.total_deducir, 105)

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
        # The exempt operations of art. 22 give the right to deduct (art. 94.Uno.1.º
        # c) LIVA), so they count in both terms
        self.assertEqual(self.model303.vat_prorate_percent, 100)
        self.assertEqual(self.model303.casilla_44, 0)

    def test_button_compute_exports_and_art_20(self):
        """Art. 104.Dos LIVA: exports, intra-community deliveries and operations
        not subject by location rules give the right to deduct; exempt operations of
        art. 20 only count in the denominator; operations not subject by art. 7 and
        the ones outside the declaration count in none."""
        self._set_general_prorate("2024-01-01", 10)
        lines = []
        for desc, price in (
            ("S_IVA21B", 200),
            # Export (E2)
            ("S_IVA0_G_E", 100),
            # Intra-community delivery (E5)
            ("S_IVA0_G_I", 100),
            # Not subject by location rules
            ("S_IVA_NS", 100),
            # Exempt by art. 20 (E1)
            ("S_IVA0_NSD", 100),
            # Not subject by art. 7
            ("S_IVA0_BC", 100),
            # One-stop shop, outside the declaration
            ("OSS_S_IVA_NS", 100),
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
        # 500 with the right to deduct of 600: 83.3, rounded up (art. 104.Dos)
        self.assertEqual(self.model303.vat_prorate_percent, 84)

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

    def test_button_compute_with_refund(self):
        """A refunded sale is taken out of the base of the definitive prorate."""
        self._set_general_prorate("2024-01-01", 10)

        def sale_lines(*lines):
            return {
                "invoice_line_ids": [
                    Command.create(
                        {
                            "name": f"Venta {price}€ {desc}",
                            "account_id": self.accounts["700000"].id,
                            "price_unit": price,
                            "quantity": 1,
                            "tax_ids": [
                                Command.link(t.id) for t in self._get_taxes(desc)
                            ],
                        }
                    )
                    for desc, price in lines
                ]
            }

        self._invoice_sale_create(
            "2024-01-01", sale_lines(("S_IVA21B", 200), ("S_IVA0", 100))
        )
        sale = self._invoice_sale_create("2024-02-01", sale_lines(("S_IVA21B", 200)))
        self._invoice_refund(sale, "2024-03-01")
        self.model303.button_compute()
        # 200 taxed (400 - 200 refunded) of 300
        self.assertEqual(self.model303.vat_prorate_percent, 67)
        # Partial refund
        sale = self._invoice_sale_create("2024-02-02", sale_lines(("S_IVA21B", 200)))
        refund = self._invoice_refund(sale, "2024-03-02")
        refund.button_draft()
        refund.write(
            {
                "invoice_line_ids": [
                    Command.update(refund.invoice_line_ids.id, {"price_unit": 100})
                ]
            }
        )
        refund.action_post()
        self.model303.button_compute()
        # 300 taxed (600 - 300 refunded) of 400
        self.assertEqual(self.model303.vat_prorate_percent, 75)

    def test_model_303_prorate_analytic_account(self):
        self._set_general_prorate("2024-01-01", 90)
        self._invoice_sale_create("2024-11-01")
        self._invoice_purchase_create("2024-11-01")
        # Analytic plans are configured by an analytic accounting manager
        analytic_plan = (
            self.env["account.analytic.plan"].sudo().create({"name": "Prorate"})
        )
        analytic_account = (
            self.env["account.analytic.account"]
            .sudo()
            .create({"name": "Prorate", "plan_id": analytic_plan.id})
        )
        self.model303_4t.write(
            {
                "vat_prorate_percent": 89,
                "prorate_analytic_account_id": analytic_account.id,
            }
        )
        self.model303_4t.button_calculate()
        # 94.5 deductible at 90 %, 1 % less
        self.assertAlmostEqual(self.model303_4t.casilla_44, -1.05)
        self.model303_4t.button_post()
        regularization_line = self.model303_4t.move_id.line_ids.filtered(
            lambda line: line.account_id == self.model303_4t.prorate_account_id
        )
        self.assertRecordValues(
            regularization_line,
            [
                {
                    "debit": 1.05,
                    "analytic_distribution": {str(analytic_account.id): 100},
                }
            ],
        )

    def test_model_303_prorate_boe_2026(self):
        """Box [44] at its position of the 2026 layout: page 01, position 985 of the
        AEAT record design DR303e26v101."""
        self._set_general_prorate("2026-01-01", 90)
        self._invoice_sale_create("2026-11-01")
        self._invoice_purchase_create("2026-11-01")
        report = self.env["l10n.es.aeat.mod303.report"].create(
            {
                "name": "9994000002026",
                "company_id": self.company.id,
                "company_vat": "123456789",
                "contact_name": "Test owner",
                "statement_type": "N",
                "support_type": "T",
                "contact_phone": "911234455",
                "year": 2026,
                "period_type": "4T",
                "date_start": "2026-10-01",
                "date_end": "2026-12-31",
                "journal_id": self.journal_misc.id,
            }
        )
        report.vat_prorate_percent = 89
        report.button_calculate()
        self.assertAlmostEqual(report.casilla_44, -1.05)
        self.assertEqual(
            report.export_config_id,
            self.env.ref("l10n_es_aeat_mod303.aeat_mod303_2026_02_main_export_config"),
        )
        wizard = (
            self.env["l10n.es.aeat.report.export_to_boe"]
            .with_context(active_id=report.id, active_model=report._name)
            .create({})
        )
        wizard.action_get_file()
        content = wizard.data.content
        page_01 = content[content.index(b"<T30301000>") :]
        self.assertEqual(page_01[984:1001], b"N0000000000000105")
