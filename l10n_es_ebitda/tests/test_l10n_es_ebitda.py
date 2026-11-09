# Copyright 2026 Acysos S.L.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo.tests.common import TransactionCase


class TestL10nEsEbitda(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.report_bottom_up = cls.env.ref(
            "account_ebitda_report.mis_report_ebitda_bottom_up"
        )
        cls.report_top_down = cls.env.ref(
            "account_ebitda_report.mis_report_ebitda_top_down"
        )
        cls.report_pro = cls.env.ref("account_ebitda_report.mis_report_ebitda_pro")

        cls.company = cls.env["res.company"].create({"name": "Test ES EBITDA Company"})
        cls.journal = cls.env["account.journal"].create(
            {
                "name": "Miscellaneous ES Journal",
                "code": "MISC",
                "type": "general",
                "company_id": cls.company.id,
            }
        )

        account_model = cls.env["account.account"]
        cls.acc_rev = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "700000",
                "name": "Ventas de mercaderías",
                "account_type": "income",
            }
        )
        cls.acc_cogs = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "600000",
                "name": "Compras de mercaderías",
                "account_type": "expense_direct_cost",
            }
        )
        cls.acc_opex = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "629000",
                "name": "Otros servicios",
                "account_type": "expense",
            }
        )
        cls.acc_da = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "681000",
                "name": "Amortización del inmovilizado material",
                "account_type": "expense_depreciation",
            }
        )
        cls.acc_taxes = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "630000",
                "name": "Impuesto sobre beneficios",
                "account_type": "expense",
            }
        )
        cls.acc_int_exp = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "662000",
                "name": "Intereses de deudas",
                "account_type": "expense",
            }
        )
        cls.acc_int_inc = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "769000",
                "name": "Otros ingresos financieros",
                "account_type": "income_other",
            }
        )
        cls.acc_exc_exp_67 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "678000",
                "name": "Gastos excepcionales",
                "account_type": "expense",
            }
        )
        cls.acc_exc_exp_69 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "691000",
                "name": "Pérdidas por deterioro del inmovilizado",
                "account_type": "expense",
            }
        )
        cls.acc_exc_inc_77 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "778000",
                "name": "Ingresos excepcionales",
                "account_type": "income_other",
            }
        )
        cls.acc_exc_inc_79 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "791000",
                "name": "Reversión del deterioro del inmovilizado",
                "account_type": "income_other",
            }
        )
        cls.acc_debt_17 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "170000",
                "name": "Deudas a largo plazo con entidades de crédito",
                "account_type": "liability_non_current",
            }
        )
        cls.acc_debt_52 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "520000",
                "name": "Deudas a corto plazo con entidades de crédito",
                "account_type": "liability_current",
            }
        )
        cls.acc_capex_20 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "206000",
                "name": "Aplicaciones informáticas",
                "account_type": "asset_fixed",
            }
        )
        cls.acc_capex_21 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "213000",
                "name": "Maquinaria",
                "account_type": "asset_fixed",
            }
        )
        cls.acc_capex_22 = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "220000",
                "name": "Inversiones en terrenos y bienes naturales",
                "account_type": "asset_fixed",
            }
        )
        cls.acc_counterpart = account_model.create(
            {
                "company_ids": cls.company.ids,
                "code": "430000",
                "name": "Clientes",
                "account_type": "asset_receivable",
            }
        )

        # Credits: 10000 (rev) + 150 (int_inc) + 200 (exc_inc_77) + 100 (exc_inc_79)
        #          + 3000 (debt_17) + 1000 (debt_52) = 14450
        # Debits: 4000 (cogs) + 1500 (opex) + 500 (da) + 400 (taxes) + 250 (int_exp)
        #         + 180 (exc_exp_67) + 120 (exc_exp_69) + 300 (capex_20)
        #         + 700 (capex_21) + 500 (capex_22) + 6000 (counterpart) = 14450
        cls.move = cls.env["account.move"].create(
            {
                "journal_id": cls.journal.id,
                "company_id": cls.company.id,
                "date": "2026-06-15",
                "line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": "Rev",
                            "account_id": cls.acc_rev.id,
                            "credit": 10000.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "COGS",
                            "account_id": cls.acc_cogs.id,
                            "debit": 4000.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "OPEX",
                            "account_id": cls.acc_opex.id,
                            "debit": 1500.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "DA",
                            "account_id": cls.acc_da.id,
                            "debit": 500.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Tax",
                            "account_id": cls.acc_taxes.id,
                            "debit": 400.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "IntExp",
                            "account_id": cls.acc_int_exp.id,
                            "debit": 250.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "IntInc",
                            "account_id": cls.acc_int_inc.id,
                            "credit": 150.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Exc67",
                            "account_id": cls.acc_exc_exp_67.id,
                            "debit": 180.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Exc69",
                            "account_id": cls.acc_exc_exp_69.id,
                            "debit": 120.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Exc77",
                            "account_id": cls.acc_exc_inc_77.id,
                            "credit": 200.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Exc79",
                            "account_id": cls.acc_exc_inc_79.id,
                            "credit": 100.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Debt17",
                            "account_id": cls.acc_debt_17.id,
                            "credit": 3000.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Debt52",
                            "account_id": cls.acc_debt_52.id,
                            "credit": 1000.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Cap20",
                            "account_id": cls.acc_capex_20.id,
                            "debit": 300.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Cap21",
                            "account_id": cls.acc_capex_21.id,
                            "debit": 700.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Cap22",
                            "account_id": cls.acc_capex_22.id,
                            "debit": 500.0,
                        },
                    ),
                    (
                        0,
                        0,
                        {
                            "name": "Counterpart",
                            "account_id": cls.acc_counterpart.id,
                            "debit": 6000.0,
                        },
                    ),
                ],
            }
        )
        cls.move._post()

    def test_01_es_report_expressions(self):
        """Ensure Spanish localized expressions are valid across all reports."""
        for report in (
            self.report_bottom_up,
            self.report_top_down,
            self.report_pro,
        ):
            instance = self.env["mis.report.instance"].create(
                {
                    "name": f"Test ES {report.name}",
                    "report_id": report.id,
                    "company_id": self.company.id,
                }
            )
            self.env["mis.report.instance.period"].create(
                {
                    "name": "Current Year",
                    "report_instance_id": instance.id,
                    "manual_date_from": "2026-01-01",
                    "manual_date_to": "2026-12-31",
                }
            )
            matrix = instance._compute_matrix()
            self.assertTrue(
                matrix,
                "The Spanish report matrix should be generated without errors",
            )

    def test_02_es_kpi_overridden_expressions(self):
        """Verify all 17 KPI records contain the Spanish PGC account prefixes."""
        for prefix in ("m1", "m2", "pro"):
            kpi_taxes = self.env.ref(f"account_ebitda_report.mis_kpi_{prefix}_taxes")
            self.assertIn("630%", kpi_taxes.expression)

            kpi_int_exp = self.env.ref(
                f"account_ebitda_report.mis_kpi_{prefix}_int_exp"
            )
            self.assertIn("66%", kpi_int_exp.expression)

            kpi_int_inc = self.env.ref(
                f"account_ebitda_report.mis_kpi_{prefix}_int_inc"
            )
            self.assertIn("76%", kpi_int_inc.expression)

            kpi_exc_exp = self.env.ref(
                f"account_ebitda_report.mis_kpi_{prefix}_exc_exp"
            )
            self.assertIn("67%", kpi_exc_exp.expression)
            self.assertIn("69%", kpi_exc_exp.expression)

            kpi_exc_inc = self.env.ref(
                f"account_ebitda_report.mis_kpi_{prefix}_exc_inc"
            )
            self.assertIn("77%", kpi_exc_inc.expression)
            self.assertIn("79%", kpi_exc_inc.expression)

        kpi_debt = self.env.ref("account_ebitda_report.mis_kpi_pro_debt")
        self.assertIn("17%", kpi_debt.expression)
        self.assertIn("52%", kpi_debt.expression)

        kpi_capex = self.env.ref("account_ebitda_report.mis_kpi_pro_capex")
        self.assertIn("20%", kpi_capex.expression)
        self.assertIn("21%", kpi_capex.expression)
        self.assertIn("22%", kpi_capex.expression)

    def test_03_es_pgc_calculation_values(self):
        """Verify EBITDA calculations using Spanish PGC account codes."""
        aep_m1 = self.report_bottom_up._prepare_aep(self.company)
        res_m1 = self.report_bottom_up.evaluate(
            aep_m1, date_from="2026-01-01", date_to="2026-12-31"
        )
        self.assertAlmostEqual(res_m1["TAXES"], 400.0)
        self.assertAlmostEqual(res_m1["INT_EXP"], 250.0)
        self.assertAlmostEqual(res_m1["INT_INC"], 150.0)
        self.assertAlmostEqual(res_m1["EXC_EXP"], 300.0)
        self.assertAlmostEqual(res_m1["EXC_INC"], 300.0)
        self.assertAlmostEqual(res_m1["DA"], 500.0)
        self.assertAlmostEqual(res_m1["EBITDA"], 4500.0)

        aep_m2 = self.report_top_down._prepare_aep(self.company)
        res_m2 = self.report_top_down.evaluate(
            aep_m2, date_from="2026-01-01", date_to="2026-12-31"
        )
        self.assertAlmostEqual(res_m2["REV"], 10000.0)
        self.assertAlmostEqual(res_m2["COGS"], 4000.0)
        self.assertAlmostEqual(res_m2["TAXES"], 400.0)
        self.assertAlmostEqual(res_m2["INT_EXP"], 250.0)
        self.assertAlmostEqual(res_m2["INT_INC"], 150.0)
        self.assertAlmostEqual(res_m2["EXC_EXP"], 300.0)
        self.assertAlmostEqual(res_m2["EXC_INC"], 300.0)
        self.assertAlmostEqual(res_m2["OPEX"], 1500.0)
        self.assertAlmostEqual(res_m2["EBITDA"], 4500.0)

        aep_pro = self.report_pro._prepare_aep(self.company)
        res_pro = self.report_pro.evaluate(
            aep_pro, date_from="2026-01-01", date_to="2026-12-31"
        )
        self.assertAlmostEqual(res_pro["REV"], 10000.0)
        self.assertAlmostEqual(res_pro["EBITDA"], 4500.0)
        self.assertAlmostEqual(res_pro["MARGIN"], 45.0)
        self.assertAlmostEqual(res_pro["ADJ_EBITDA"], 4500.0)
        self.assertAlmostEqual(res_pro["DEBT"], 4000.0)
        self.assertAlmostEqual(res_pro["CAPEX"], 1500.0)
        self.assertAlmostEqual(res_pro["FCF"], 2350.0)
